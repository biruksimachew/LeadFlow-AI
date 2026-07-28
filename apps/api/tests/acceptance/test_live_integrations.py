from __future__ import annotations

from uuid import uuid4

import pytest


pytestmark = pytest.mark.live


def key(prefix: str) -> str:
    return f"accept-live-{prefix}-{uuid4().hex}"


def test_09_n8n_rejects_missing_ingress_token(
    harness,
    require_live,
) -> None:
    payload = harness.lead_payload(
        prefix="n8n-no-auth",
    )

    response = harness.n8n_response(
        payload,
        idempotency_key=key("no-auth"),
        include_ingress_token=False,
    )

    assert response.status_code == 403

    lead = harness.fetchrow(
        """
        select id
        from public.leads
        where email_normalized = $1;
        """,
        payload["email"].lower(),
    )

    assert lead is None


def test_10_n8n_acknowledges_then_completes_asynchronously(
    harness,
    require_live,
) -> None:
    payload = harness.lead_payload(
        prefix="n8n-async",
    )

    response = harness.n8n_response(
        payload,
        idempotency_key=key("async"),
    )

    assert response.status_code == 202
    assert (
        response.elapsed.total_seconds()
        < 3.0
    )

    receipt = response.json()

    assert receipt["success"] is True
    assert receipt["stage"] == "INTAKE"
    assert receipt["status"] == "RECEIVED"
    assert receipt["continue_processing"] is True

    assert receipt["lead_id"]
    assert receipt["intake_id"]
    assert receipt["correlation_id"]

    assert "workflow_outcome" not in receipt
    assert "completed" not in receipt

    def completed_probe():
        row = harness.fetchrow(
            """
            select
                l.status,
                l.assigned_owner_id,
                l.crm_sync_status,
                l.hubspot_contact_id,
                l.hubspot_deal_id,
                (
                    select count(*)::int
                    from public.communications c
                    where c.lead_id = l.id
                ) as communication_count
            from public.leads l
            where l.id = $1::uuid;
            """,
            receipt["lead_id"],
        )

        if row is None:
            return None

        if (
            row["status"]
            not in {
                "QUALIFIED_WARM",
                "QUALIFIED_HOT",
            }
        ):
            return None

        if row["assigned_owner_id"] is None:
            return None

        if row["crm_sync_status"] != "SUCCEEDED":
            return None

        if row["hubspot_contact_id"] is None:
            return None

        if row["hubspot_deal_id"] is None:
            return None

        if row["communication_count"] < 1:
            return None

        return row

    completed = harness.wait_until(
        completed_probe,
        description=(
            "the acknowledged lead to finish "
            "routing, CRM sync, and actions"
        ),
    )

    assert completed["status"] in {
        "QUALIFIED_WARM",
        "QUALIFIED_HOT",
    }


def test_11_n8n_duplicate_branch_stops(
    harness,
    require_live,
) -> None:
    payload = harness.lead_payload(
        prefix="n8n-duplicate",
    )

    first = harness.n8n(
        payload,
        idempotency_key=key("dup-seed"),
    )

    assert first["stage"] == "INTAKE"
    assert first["continue_processing"] is True
    assert first["duplicate"] is False

    duplicate = harness.n8n(
        payload,
        idempotency_key=key("dup-check"),
    )

    assert duplicate["stage"] == "INTAKE"
    assert duplicate["duplicate"] is True
    assert (
        duplicate["continue_processing"]
        is False
    )
    assert (
        duplicate["lead_id"]
        == first["lead_id"]
    )


def test_12_n8n_review_branch_stops_before_crm(
    harness,
    require_live,
) -> None:
    payload = harness.lead_payload(
        prefix="n8n-review",
        service_type="other",
        message=(
            "I need someone to inspect damage above "
            "my garage and determine what kind of repair "
            "is required."
        ),
    )

    receipt = harness.n8n(
        payload,
        idempotency_key=key("review"),
    )

    assert receipt["stage"] == "INTAKE"
    assert receipt["continue_processing"] is True

    def review_probe():
        row = harness.fetchrow(
            """
            select
                status,
                assigned_owner_id,
                hubspot_contact_id,
                hubspot_deal_id
            from public.leads
            where id = $1::uuid;
            """,
            receipt["lead_id"],
        )

        if (
            row is None
            or row["status"]
            != "REVIEW_REQUIRED"
        ):
            return None

        return row

    lead = harness.wait_until(
        review_probe,
        description=(
            "the lead to enter human review"
        ),
    )

    assert lead["assigned_owner_id"] is None
    assert lead["hubspot_contact_id"] is None
    assert lead["hubspot_deal_id"] is None


def test_13_crm_replay_preserves_provider_ids(
    harness,
    require_live,
) -> None:
    payload = harness.lead_payload(
        prefix="crm-replay",
    )

    intake = harness.intake(
        payload,
        idempotency_key=key("crm"),
    )

    harness.stage(
        intake["lead_id"],
        "qualify",
    )
    harness.stage(
        intake["lead_id"],
        "route",
    )

    harness.stage(
        intake["lead_id"],
        "crm",
    )

    before = harness.fetchrow(
        """
        select
            crm_sync_status,
            hubspot_contact_id,
            hubspot_deal_id
        from public.leads
        where id = $1::uuid;
        """,
        intake["lead_id"],
    )

    harness.stage(
        intake["lead_id"],
        "crm",
    )

    after = harness.fetchrow(
        """
        select
            crm_sync_status,
            hubspot_contact_id,
            hubspot_deal_id
        from public.leads
        where id = $1::uuid;
        """,
        intake["lead_id"],
    )

    assert before["crm_sync_status"] == "SUCCEEDED"
    assert after["crm_sync_status"] == "SUCCEEDED"

    assert (
        before["hubspot_contact_id"]
        == after["hubspot_contact_id"]
    )
    assert (
        before["hubspot_deal_id"]
        == after["hubspot_deal_id"]
    )


def test_14_action_replay_does_not_duplicate_communications(
    harness,
    require_live,
) -> None:
    payload = harness.lead_payload(
        prefix="action-replay",
    )

    intake = harness.intake(
        payload,
        idempotency_key=key("actions"),
    )

    harness.stage(
        intake["lead_id"],
        "qualify",
    )
    harness.stage(
        intake["lead_id"],
        "route",
    )
    harness.stage(
        intake["lead_id"],
        "crm",
    )

    harness.stage(
        intake["lead_id"],
        "actions",
    )

    first_rows = harness.fetch(
        """
        select
            channel,
            template_key,
            status
        from public.communications
        where lead_id = $1::uuid
        order by channel, template_key;
        """,
        intake["lead_id"],
    )

    harness.stage(
        intake["lead_id"],
        "actions",
    )

    second_rows = harness.fetch(
        """
        select
            channel,
            template_key,
            status
        from public.communications
        where lead_id = $1::uuid
        order by channel, template_key;
        """,
        intake["lead_id"],
    )

    first = [
        (
            row["channel"],
            row["template_key"],
            row["status"],
        )
        for row in first_rows
    ]

    second = [
        (
            row["channel"],
            row["template_key"],
            row["status"],
        )
        for row in second_rows
    ]

    assert first
    assert first == second


def test_15_cold_without_consent_never_sends_nurture(
    harness,
    require_live,
) -> None:
    identity = harness.new_identity(
        "cold-no-consent",
    )

    payload = {
        "full_name": "Cold Acceptance Lead",
        "email": identity.email,
        "phone": None,
        "service_type": "electrical",
        "location": "North District, 10021",
        "urgency": "unknown",
        "message": (
            "One electrical outlet has stopped working."
        ),
        "source": "manual",
        "preferred_contact": "unknown",
        "consent_marketing": False,
    }

    intake = harness.intake(
        payload,
        idempotency_key=key("cold"),
    )

    qualification = harness.stage(
        intake["lead_id"],
        "qualify",
    )

    assert qualification["status"] == "COLD"

    harness.stage(
        intake["lead_id"],
        "route",
    )
    harness.stage(
        intake["lead_id"],
        "crm",
    )
    harness.stage(
        intake["lead_id"],
        "actions",
    )

    rows = harness.fetch(
        """
        select
            status
        from public.communications
        where lead_id = $1::uuid
          and template_key = 'cold_nurture_email';
        """,
        intake["lead_id"],
    )

    assert not any(
        row["status"] == "SENT"
        for row in rows
    )


def test_16_n8n_outside_area_stops_without_side_effects(
    harness,
    require_live,
) -> None:
    payload = harness.lead_payload(
        prefix="n8n-outside",
        location="South District, 99999",
    )

    receipt = harness.n8n(
        payload,
        idempotency_key=key("outside"),
    )

    assert receipt["stage"] == "INTAKE"
    assert receipt["continue_processing"] is True

    def disqualified_probe():
        row = harness.fetchrow(
            """
            select
                status,
                assigned_owner_id,
                hubspot_contact_id,
                hubspot_deal_id
            from public.leads
            where id = $1::uuid;
            """,
            receipt["lead_id"],
        )

        if (
            row is None
            or row["status"]
            != "DISQUALIFIED"
        ):
            return None

        return row

    lead = harness.wait_until(
        disqualified_probe,
        description=(
            "the lead to become disqualified"
        ),
    )

    assert lead["assigned_owner_id"] is None
    assert lead["hubspot_contact_id"] is None
    assert lead["hubspot_deal_id"] is None
