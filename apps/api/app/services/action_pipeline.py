from app.providers.communications.base import (
    CommunicationProviderError,
)
from app.config import settings

from app.providers.communications.factory import (
    build_communication_provider,
)

from app.repositories.actions import (
    communication_completed,
    get_or_create_booking_link,
    get_template,
    persist_communication_failed,
    persist_communication_sent,
    persist_communication_skipped,
)

async def _send_template(
    pool,
    *,
    provider,
    lead_id,
    correlation_id: str,
    template_key: str,
    recipient: str,
    values: dict,
    consent_basis: str,
) -> None:

    async with pool.acquire() as connection:

        if await communication_completed(
            connection,
            lead_id=lead_id,
            channel=values["channel"],
            template_key=template_key,
        ):
            return

        template = await get_template(
            connection,
            template_key,
        )

    subject = None

    if template["subject_template"]:
        subject = (
            template["subject_template"]
            .format(**values)
        )

    body = (
        template["body_template"]
        .format(**values)
    )

    channel = template["channel"]

    provider_name = {
        "email": "resend",
        "sms": "twilio_mock",
        "slack": "slack",
    }.get(
        channel,
        channel,
    )

    try:

        if channel == "email":

            result = await provider.send_email(
                to=recipient,
                subject=subject or "",
                body=body,
                idempotency_key=(
                    f"lead/{lead_id}/{template_key}"
                ),
            )

        elif channel == "sms":

            result = await provider.send_sms(
                to=recipient,
                body=body,
            )

        elif channel == "slack":

            result = await provider.send_slack(
                recipient=recipient,
                body=body,
            )

        else:
            raise RuntimeError(
                f"Unsupported channel: {channel}"
            )

    except CommunicationProviderError as exc:

        error_code = getattr(
            exc,
            "code",
            "COMMUNICATION_PROVIDER_ERROR",
        )

        error_message = getattr(
            exc,
            "message",
            str(exc),
        )

        retryable = bool(
            getattr(
                exc,
                "retryable",
                False,
            )
        )

        async with pool.acquire() as connection:

            async with connection.transaction():

                await persist_communication_failed(
                    connection,
                    lead_id=lead_id,
                    correlation_id=correlation_id,
                    channel=channel,
                    template_key=template_key,
                    recipient=recipient,
                    provider=provider_name,
                    error_code=error_code,
                    error_message=error_message,
                    retryable=retryable,
                    consent_basis=consent_basis,
                )

        # Preserve existing continuation behavior:
        # downstream workflow records the overall failure.
        raise

    async with pool.acquire() as connection:

        async with connection.transaction():

            await persist_communication_sent(
                connection,
                lead_id=lead_id,
                correlation_id=correlation_id,
                channel=channel,
                template_key=template_key,
                recipient=recipient,
                provider=result.provider,
                provider_message_id=(
                    result.provider_message_id
                ),
                payload=result.payload,
                consent_basis=consent_basis,
            )


async def run_post_qualification_actions(
    pool,
    *,
    lead_id,
    correlation_id: str,
    lead,
    score: int,
    final_status: str,
    owner_id: str | None,
) -> None:

    provider = build_communication_provider()

    first_name = (
        lead.full_name.split()[0]
        if lead.full_name
        else "there"
    )

    values = {
        "first_name": first_name,
        "service_type": (
            lead.service_type.value
        ),
        "score": score,
        "location": lead.location_raw,
        "source": lead.source.value,
        "owner_id": (
            owner_id or "fallback queue"
        ),
        "lead_url": (
            f"{settings.dashboard_base_url}"
            f"/leads/{lead_id}"
        ),
        "booking_url": "",
        "channel": "",
    }

    # ========================================================
    # HOT
    # ========================================================

    if final_status == "QUALIFIED_HOT":

        async with pool.acquire() as connection:

            async with connection.transaction():

                booking_url = (
                    await get_or_create_booking_link(
                        connection,
                        lead_id=lead_id,
                        correlation_id=correlation_id,
                        booking_url=(
                            settings.booking_base_url
                        ),
                    )
                )

        values["booking_url"] = booking_url

        if lead.email_normalized:

            values["channel"] = "email"

            await _send_template(
                pool,
                provider=provider,
                lead_id=lead_id,
                correlation_id=correlation_id,
                template_key="hot_email",
                recipient=lead.email_normalized,
                values=values,
                consent_basis="transactional",
            )

        if lead.phone_e164:

            values["channel"] = "sms"

            await _send_template(
                pool,
                provider=provider,
                lead_id=lead_id,
                correlation_id=correlation_id,
                template_key="hot_sms",
                recipient=lead.phone_e164,
                values=values,
                consent_basis="transactional",
            )

        values["channel"] = "slack"

        await _send_template(
            pool,
            provider=provider,
            lead_id=lead_id,
            correlation_id=correlation_id,
            template_key="hot_slack_channel",
            recipient=settings.slack_hot_channel,
            values=values,
            consent_basis="internal",
        )

        if settings.slack_owner_user_id:

            await _send_template(
                pool,
                provider=provider,
                lead_id=lead_id,
                correlation_id=correlation_id,
                template_key="hot_slack_owner",
                recipient=(
                    settings.slack_owner_user_id
                ),
                values=values,
                consent_basis="internal",
            )
        return

    # ========================================================
    # WARM
    # ========================================================

    if final_status == "QUALIFIED_WARM":

        if lead.email_normalized:

            values["channel"] = "email"

            await _send_template(
                pool,
                provider=provider,
                lead_id=lead_id,
                correlation_id=correlation_id,
                template_key="warm_email",
                recipient=lead.email_normalized,
                values=values,
                consent_basis="transactional",
            )

        return

    # ========================================================
    # COLD
    # ========================================================

    if final_status == "COLD":

        if not lead.consent_marketing:

            async with pool.acquire() as connection:

                async with connection.transaction():

                    await persist_communication_skipped(
                        connection,
                        lead_id=lead_id,
                        correlation_id=correlation_id,
                        channel="email",
                        template_key=(
                            "cold_nurture_email"
                        ),
                        reason=(
                            "marketing_consent_absent"
                        ),
                    )

            return

        if lead.email_normalized:

            values["channel"] = "email"

            await _send_template(
                pool,
                provider=provider,
                lead_id=lead_id,
                correlation_id=correlation_id,
                template_key="cold_nurture_email",
                recipient=lead.email_normalized,
                values=values,
                consent_basis=(
                    "marketing_consent"
                ),
            )