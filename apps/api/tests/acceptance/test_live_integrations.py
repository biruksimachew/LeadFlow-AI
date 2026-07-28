from __future__ import annotations

from uuid import uuid4

import pytest


pytestmark = pytest.mark.live


def key(prefix: str) -> str:
    return f"accept-live-{prefix}-{uuid4().hex}"


def test_09_n8n_happy_path_completes(
    harness,
    require_live,
) -> None:
    payload = harness.lead_payload(
        prefix="n8n-happy",
    )

    result = harness.n8n(
        payload,
        idempotency_key=key("happy"),
    )

    assert result["success"] is True
    assert (
        result["workflow_outcome"]
        == "COMPLETED"
    )
    assert result["completed"] is True
    assert (
        result["status"]
        in {
            "QUALIFIED_WARM",
            "QUALIFIED_HOT",
        }
    )


def test_10_n8n_duplicate_branch_stops(
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

    assert (
        first["workflow_outcome"]
        == "COMPLETED"
    )

    duplicate = harness.n8n(
        payload,
        idempotency_key=key("dup-check"),
    )

    assert duplicate["duplicate"] is True
    assert (
        duplicate["continue_processing"]
        is False
    )
    assert (
        duplicate["workflow_outcome"]
        == "INTAKE_STOPPED"
    )


def test_11_n8n_review_branch_stops_before_crm(
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

    result = harness.n8n(
        payload,
        idempotency_key=key("review"),
    )

    assert result["status"] == "REVIEW_REQUIRED"
    assert result["review_required"] is True
    assert (
        result["workflow_outcome"]
        == "REVIEW_REQUIRED"
    )

    lead = harness.fetchrow(
        """
        select
            assigned_owner_id,
            hubspot_contact_id,
            hubspot_deal_id
        from public.leads
        where id = $1::uuid;
        """,
        result["lead_id"],
    )

    assert lead["assigned_owner_id"] is None
    assert lead["hubspot_contact_id"] is None
    assert lead["hubspot_deal_id"] is None


def test_12_crm_replay_preserves_provider_ids(
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


def test_13_action_replay_does_not_duplicate_communications(
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


def test_14_cold_without_consent_never_sends_nurture(
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


def test_15_n8n_outside_area_stops_without_side_effects(
    harness,
    require_live,
) -> None:
    payload = harness.lead_payload(
        prefix="n8n-outside",
        location="South District, 99999",
    )

    result = harness.n8n(
        payload,
        idempotency_key=key("outside"),
    )

    assert result["status"] == "DISQUALIFIED"
    assert (
        result["continue_processing"]
        is False
    )

    lead = harness.fetchrow(
        """
        select
            assigned_owner_id,
            hubspot_contact_id,
            hubspot_deal_id
        from public.leads
        where id = $1::uuid;
        """,
        result["lead_id"],
    )

    assert lead["assigned_owner_id"] is None
    assert lead["hubspot_contact_id"] is None
    assert lead["hubspot_deal_id"] is None
