import hashlib
import hmac
import json
import os
import urllib.error
import urllib.request


WEBHOOK_URL = (
    "http://localhost:8000/api/v1/webhooks/calcom"
)

SECRET = os.environ["CAL_WEBHOOK_SECRET"]



ATTENDEE_EMAIL = os.getenv(
    "CAL_TEST_ATTENDEE_EMAIL",
    "cal.webhook.test@example.com",
)

BOOKING_UID = os.getenv(
    "CAL_TEST_BOOKING_UID",
    "cal-leadflow-test-001",
)

payload = {
    "triggerEvent": "BOOKING_CREATED",
    "createdAt": "2026-07-25T18:00:00.000Z",
    "payload": {
        "uid": BOOKING_UID,
        "bookingId": 9001,
        "title": "NorthStar Service Visit",
        "startTime": (
            "2026-07-27T10:00:00.000Z"
        ),
        "endTime": (
            "2026-07-27T10:30:00.000Z"
        ),
        "attendees": [
            {
                "name": "Nora Collins",
                "email": ATTENDEE_EMAIL,
                "timeZone": (
                    "America/New_York"
                ),
            }
        ],
        "organizer": {
            "name": (
                "NorthStar Home Services"
            ),
            "timeZone": (
                "America/New_York"
            ),
        },
    },
}


# IMPORTANT:
# These exact bytes are both signed AND sent.
body = json.dumps(
    payload,
    separators=(",", ":"),
).encode("utf-8")


signature = hmac.new(
    SECRET.encode("utf-8"),
    body,
    hashlib.sha256,
).hexdigest()


print(
    "Secret loaded:",
    bool(SECRET),
)

print(
    "Body length:",
    len(body),
)

print(
    "Signature:",
    signature[:12] + "...",
)


request = urllib.request.Request(
    WEBHOOK_URL,
    data=body,
    method="POST",
    headers={
        "Content-Type": "application/json",
        "x-cal-signature-256": signature,
    },
)


try:

    with urllib.request.urlopen(
        request,
        timeout=15,
    ) as response:

        print(
            "HTTP:",
            response.status,
        )

        print(
            response.read().decode(
                "utf-8"
            )
        )

except urllib.error.HTTPError as exc:

    print(
        "HTTP ERROR:",
        exc.code,
    )

    print(
        exc.read().decode(
            "utf-8"
        )
    )