from __future__ import annotations

from uuid import uuid4


def key(prefix: str) -> str:
    return f"accept-{prefix}-{uuid4().hex}"


def test_01_demo_configuration_is_provisioned(
    harness,
) -> None:
    required_qualification = {
        "service_area_points",
        "supported_service_points",
        "urgency_points",
        "data_completeness_points",
        "source_quality_points",
        "score_bands",
        "timeline_readiness_points",
    }

    qualification_rows = harness.fetch(
        """
        select config_key
        from public.qualification_config
        where active = true;
        """
    )

    qualification_keys = {
        row["config_key"]
        for row in qualification_rows
    }

    assert (
        required_qualification
        <= qualification_keys
    )

    required_templates = {
        "hot_email",
        "warm_email",
        "cold_nurture_email",
        "hot_sms",
        "hot_slack_channel",
        "hot_slack_owner",
    }

    template_rows = harness.fetch(
        """
        select template_key
        from public.message_templates
        where active = true;
        """
    )

    template_keys = {
        row["template_key"]
        for row in template_rows
    }

    assert (
        required_templates
        <= template_keys
    )

    routing_rows = harness.fetch(
        """
        select
            rule_key,
            target_owner_id,
            active,
            available
        from public.routing_rules
        where rule_key is not null;
        """
    )

    canonical_keys = {
        "north_plumbing_primary",
        "north_electrical_primary",
        "north_hvac_primary",
        "north_appliance_repair_primary",
    }

    active_keys = {
        row["rule_key"]
        for row in routing_rows
        if (
            row["active"]
            and row["available"]
            and row["target_owner_id"]
            != "UNCONFIGURED"
        )
    }

    assert canonical_keys <= active_keys

    fallback = harness.fetchrow(
        """
        select fallback_owner_id
        from public.routing_config
        where config_key = 'default';
        """
    )

    assert fallback is not None
    assert (
        fallback["fallback_owner_id"]
        != "UNCONFIGURED"
    )


def test_02_same_event_replays_same_lead(
    harness,
) -> None:
    payload = harness.lead_payload(
        prefix="replay",
    )

    idempotency_key = key("replay")

    first = harness.intake(
        payload,
        idempotency_key=idempotency_key,
    )

    second = harness.intake(
        payload,
        idempotency_key=idempotency_key,
    )

    assert first["lead_id"] == second["lead_id"]
    assert second["replayed"] is True
    assert second["duplicate"] is False


def test_03_same_customer_new_event_is_duplicate(
    harness,
) -> None:
    payload = harness.lead_payload(
        prefix="duplicate",
    )

    original = harness.intake(
        payload,
        idempotency_key=key("dup-original"),
    )

    duplicate = harness.intake(
        payload,
        idempotency_key=key("dup-second"),
    )

    assert original["duplicate"] is False
    assert duplicate["duplicate"] is True
    assert duplicate["continue_processing"] is False


def test_04_warm_lead_qualifies_deterministically(
    harness,
) -> None:
    payload = harness.lead_payload(
        prefix="warm",
        urgency="within_7_days",
    )

    intake = harness.intake(
        payload,
        idempotency_key=key("warm"),
    )

    qualification = harness.stage(
        intake["lead_id"],
        "qualify",
    )

    assert (
        qualification["status"]
        == "QUALIFIED_WARM"
    )

    assert (
        55
        <= qualification["score"]
        < 80
    )

    assert (
        qualification[
            "continue_processing"
        ]
        is True
    )


def test_05_unsupported_service_requires_review(
    harness,
) -> None:
    payload = harness.lead_payload(
        prefix="review",
        service_type="other",
        message=(
            "I need someone to inspect damage above "
            "my garage and determine the correct trade."
        ),
    )

    intake = harness.intake(
        payload,
        idempotency_key=key("review"),
    )

    qualification = harness.stage(
        intake["lead_id"],
        "qualify",
    )

    assert (
        qualification["status"]
        == "REVIEW_REQUIRED"
    )

    assert (
        qualification[
            "review_required"
        ]
        is True
    )

    assert (
        qualification[
            "continue_processing"
        ]
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
        intake["lead_id"],
    )

    assert lead["assigned_owner_id"] is None
    assert lead["hubspot_contact_id"] is None
    assert lead["hubspot_deal_id"] is None


def test_06_outside_service_area_is_disqualified(
    harness,
) -> None:
    payload = harness.lead_payload(
        prefix="outside",
        location="South District, 99999",
    )

    intake = harness.intake(
        payload,
        idempotency_key=key("outside"),
    )

    qualification = harness.stage(
        intake["lead_id"],
        "qualify",
    )

    assert (
        qualification["status"]
        == "DISQUALIFIED"
    )

    assert (
        qualification[
            "continue_processing"
        ]
        is False
    )


def test_07_emergency_with_explicit_booking_is_hot(
    harness,
) -> None:
    payload = harness.lead_payload(
        prefix="hot",
        service_type="electrical",
        urgency="emergency",
        message=(
            "This is an electrical emergency. "
            "Several outlets are sparking and "
            "I need an electrician. I want to "
            "book an appointment today."
        ),
    )

    intake = harness.intake(
        payload,
        idempotency_key=key("hot"),
    )

    qualification = harness.stage(
        intake["lead_id"],
        "qualify",
    )

    assert (
        qualification["status"]
        == "QUALIFIED_HOT"
    )

    assert qualification["score"] >= 80

    result = harness.fetchrow(
        """
        select
            deterministic_score,
            qualification_status,
            final_status,
            ai_confidence,
            ai_review_reasons
        from public.qualification_results
        where lead_id = $1::uuid
        order by created_at desc
        limit 1;
        """,
        intake["lead_id"],
    )

    assert (
        result["qualification_status"]
        == "QUALIFIED_HOT"
    )

    assert (
        result["final_status"]
        == "QUALIFIED_HOT"
    )

    assert (
        float(result["ai_confidence"])
        >= 0.70
    )

    assert (
        list(result["ai_review_reasons"])
        == []
    )



def test_08_low_ai_confidence_forces_review(
    harness,
) -> None:
    payload = harness.lead_payload(
        prefix="low-confidence",
        service_type="electrical",
        urgency="emergency",
        message=(
            "This is an emergency. "
            "I want to book an appointment today "
            "and have a technician come out."
        ),
    )

    intake = harness.intake(
        payload,
        idempotency_key=key(
            "low-confidence",
        ),
    )

    qualification = harness.stage(
        intake["lead_id"],
        "qualify",
    )

    result = harness.fetchrow(
        """
        select
            deterministic_score,
            qualification_status,
            final_status,
            ai_confidence,
            ai_review_reasons
        from public.qualification_results
        where lead_id = $1::uuid
        order by created_at desc
        limit 1;
        """,
        intake["lead_id"],
    )

    assert (
        result["qualification_status"]
        == "QUALIFIED_HOT"
    )

    assert (
        result["deterministic_score"]
        >= 80
    )

    assert (
        float(result["ai_confidence"])
        < 0.70
    )

    assert (
        "LOW_AI_CONFIDENCE"
        in result["ai_review_reasons"]
    )

    assert (
        result["final_status"]
        == "REVIEW_REQUIRED"
    )

    assert (
        qualification["status"]
        == "REVIEW_REQUIRED"
    )

    assert (
        qualification["review_required"]
        is True
    )

    assert (
        qualification[
            "continue_processing"
        ]
        is False
    )

def test_09_routing_uses_provisioned_owner(
    harness,
) -> None:
    payload = harness.lead_payload(
        prefix="routing",
    )

    intake = harness.intake(
        payload,
        idempotency_key=key("routing"),
    )

    qualification = harness.stage(
        intake["lead_id"],
        "qualify",
    )

    assert (
        qualification[
            "continue_processing"
        ]
        is True
    )

    harness.stage(
        intake["lead_id"],
        "route",
    )

    lead = harness.fetchrow(
        """
        select
            assigned_owner_id,
            assigned_queue,
            routing_rule_id
        from public.leads
        where id = $1::uuid;
        """,
        intake["lead_id"],
    )

    assert lead["routing_rule_id"] is not None
    assert lead["assigned_queue"] == "electrical"

    if harness.default_owner_id:
        assert (
            lead["assigned_owner_id"]
            == harness.default_owner_id
        )
    else:
        assert lead["assigned_owner_id"]
