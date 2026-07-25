import hashlib
import hmac
import json

import asyncpg

from fastapi import (
    APIRouter,
    Header,
    HTTPException,
    Request,
    status,
)

from app.config import settings

from app.providers.crm.base import (
    CRMProviderError,
)

from app.providers.crm.factory import (
    build_crm_provider,
)

from app.repositories.appointments import (
    AppointmentLeadNotFound,
    process_booking_created,
)

import logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/webhooks",
    tags=["Webhooks"],
)


def verify_cal_signature(
    raw_body: bytes,
    signature: str | None,
) -> bool:

    if not settings.cal_webhook_secret:
        return False

    if not signature:
        return False

    expected = hmac.new(
        settings.cal_webhook_secret.encode(
            "utf-8"
        ),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        expected,
        signature,
    )


@router.post("/calcom")
async def receive_calcom_webhook(
    request: Request,
    x_cal_signature_256: str | None = Header(
        default=None,
        alias="x-cal-signature-256",
    ),
) -> dict:

    raw_body = await request.body()

    if not verify_cal_signature(
        raw_body,
        x_cal_signature_256,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_CAL_SIGNATURE",
                "message": (
                    "Cal.com webhook signature "
                    "verification failed."
                ),
            },
        )

    try:
        event = json.loads(raw_body)

    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_WEBHOOK_JSON",
            },
        ) from exc

    trigger = event.get("triggerEvent")

    if trigger != "BOOKING_CREATED":
        return {
            "success": True,
            "ignored": True,
            "trigger": trigger,
        }

    payload = event.get("payload") or {}

    attendees = payload.get("attendees") or []

    attendee = (
        attendees[0]
        if attendees
        else {}
    )

    attendee_email = attendee.get("email")

    external_id = (
        payload.get("uid")
        or payload.get("bookingUid")
        or payload.get("bookingId")
    )

    start_at = payload.get("startTime")
    end_at = payload.get("endTime")

    timezone = (
        attendee.get("timeZone")
        or (
            payload.get("organizer")
            or {}
        ).get("timeZone")
    )

    if not all(
        [
            attendee_email,
            external_id,
            start_at,
            end_at,
        ]
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": (
                    "CAL_WEBHOOK_FIELDS_MISSING"
                ),
                "message": (
                    "Booking webhook lacks attendee, "
                    "UID or appointment time."
                ),
            },
        )

    try:

        async with (
            request.app.state.db_pool.acquire()
            as connection
        ):

            async with connection.transaction():

                booking = (
                    await process_booking_created(
                        connection,
                        external_appointment_id=(
                            str(external_id)
                        ),
                        attendee_email=attendee_email,
                        start_at=start_at,
                        end_at=end_at,
                        timezone=timezone,
                        provider_payload=event,
                    )
                )

    except AppointmentLeadNotFound as exc:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": (
                    "APPOINTMENT_LEAD_NOT_FOUND"
                ),
                "message": str(exc),
            },
        ) from exc

    except asyncpg.PostgresError as exc:

        logger.exception(
            "Appointment webhook database failure. "
            "external_appointment_id=%s attendee_email=%s",
            external_id,
            attendee_email,
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "APPOINTMENT_DATABASE_ERROR",
            },
        ) from exc
    # Update the existing HubSpot deal.
    provider = None

    try:

        provider = build_crm_provider()

        await provider.upsert_deal(
            leadflow_lead_id=str(
                booking["lead_id"]
            ),
            properties={
                "leadflow_automation_status": (
                    "APPOINTMENT_BOOKED"
                ),
            },
        )

    except CRMProviderError as exc:

        # Return 503 so Cal.com can retry. The local booking
        # state is already safely persisted and replay-safe.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": exc.code,
                "message": (
                    "Appointment stored, but HubSpot "
                    "could not be updated."
                ),
            },
        ) from exc

    finally:

        if (
            provider is not None
            and hasattr(provider, "close")
        ):
            await provider.close()

    return {
        "success": True,
        "trigger": trigger,
        "lead_id": str(booking["lead_id"]),
        "replayed": booking["replayed"],
    }