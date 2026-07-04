import os
import logging
from google import genai
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AgreementSchema(BaseModel):
    subject_of_lease: str = Field(description="A formal paragraph identifying the property being leased (type, address, what is included) — Clause 1.")
    term_and_duration: str = Field(description="A paragraph stating the lease start date, minimum stay, and renewal/termination terms — Clause 2.")
    rent_and_payment_terms: str = Field(description="A paragraph covering the monthly rent amount, payment frequency/method, and deposit handling — Clause 3.")
    landlord_obligations: str = Field(description="A plain-text bulleted list (one item per line, no markdown symbols) of the landlord's obligations — Clause 4.")
    tenant_obligations: str = Field(description="A plain-text bulleted list (one item per line, no markdown symbols) of the tenant's obligations, drawn from the property's house rules — Clause 5.")
    general_provisions: str = Field(description="A plain-text numbered or bulleted list of general legal provisions: assignment/subletting restrictions, breach/termination consequences, governing law, dispute resolution — Clause 6.")


def _build_poster_data(poster) -> dict:
    return {
        "full_name": poster.full_name,
        "email": poster.email,
        "phone_number": poster.phone_number or "Not provided",
    }


def _build_tenant_data(tenant) -> dict:
    return {
        "full_name": tenant.full_name,
        "email": tenant.email,
        "phone_number": tenant.phone_number or "Not provided",
    }


def _active_house_rules(listing) -> list:
    house_rule_fields = [
        'no_smoking', 'smoking_outside_ok', 'no_alcohol', 'no_vaping',
        'pets_allowed', 'dogs_allowed', 'cats_allowed', 'no_pets',
        'quiet_after_10', 'early_sleepers', 'no_loud_music', 'no_parties', 'calm_environment', 'no_calls_common',
        'shared_cleaning', 'no_shoes_inside', 'respect_spaces', 'clean_bathroom', 'separate_recycling',
        'no_overnight_guests', 'guests_with_notice', 'curfew_midnight', 'no_gatherings',
        'fully_furnished', 'no_food_in_rooms', 'must_cook', 'vegetarian_house',
        'muslims_only', 'christians_only', 'all_religions_ok', 'halal_kitchen', 'prayer_space',
        'males_only', 'females_only', 'students_only', 'professionals_only', 'expats_welcome', 'no_children',
    ]
    return [field.replace('_', ' ') for field in house_rule_fields if getattr(listing, field)]


def _build_listing_data(listing) -> dict:
    return {
        "title": listing.title,
        "address": ", ".join(filter(None, [listing.street, listing.district, listing.city, listing.country])),
        "listing_type": listing.get_listing_type_display(),
        "monthly_rent": float(listing.price),
        "rent_negotiable": listing.rent_negotiable,
        "available_from": listing.available_from.isoformat(),
        "min_stay_months": listing.get_min_stay_months_display(),
        "max_occupants": listing.max_occupants,
        "security_deposit_required": listing.security_deposit,
        "payment_frequency": "Monthly" if listing.monthly_payment else ("Quarterly" if listing.quarterly_payment else "As agreed"),
        "online_payment_accepted": listing.online_payment,
        "check_in_time": listing.check_in_time.isoformat() if listing.check_in_time else None,
        "check_out_time": listing.check_out_time.isoformat() if listing.check_out_time else None,
        "active_house_rules": _active_house_rules(listing),
    }


def _fallback_result(listing, reason: str) -> dict:
    logger.warning("Gemini agreement generation unavailable: %s", reason)
    rules = _active_house_rules(listing)[:6]
    rules_text = "\n".join(f"- Tenant shall observe: {r}." for r in rules) or "- No specific house rules were listed for this property."
    deposit_line = (
        " A security deposit is required, as agreed upon separately between the parties."
        if listing.security_deposit else ""
    )

    return {
        "subject_of_lease": f'The Landlord agrees to lease to the Tenant the property described as '
                             f'"{listing.title}" ({listing.get_listing_type_display()}), located at '
                             f'{", ".join(filter(None, [listing.street, listing.district, listing.city, listing.country]))}, '
                             f'for residential use only, together with any fixtures and furnishings agreed between the parties.',
        "term_and_duration": f"This lease shall commence on {listing.available_from.isoformat()} for a minimum "
                              f"term of {listing.get_min_stay_months_display()}. Thereafter, the lease shall "
                              f"continue on a month-to-month basis unless terminated by either party with at "
                              f"least thirty (30) days' prior written notice.",
        "rent_and_payment_terms": f"The Tenant shall pay the Landlord a monthly rent of {listing.price}, "
                                   f"payable on the agreed due date each month.{deposit_line}",
        "landlord_obligations": (
            "- Deliver the property in a habitable and clean condition.\n"
            "- Carry out necessary repairs and maintenance not caused by the Tenant's negligence.\n"
            "- Not interfere with the Tenant's quiet use and enjoyment of the property during the lease term."
        ),
        "tenant_obligations": rules_text + "\n- Use the property solely for lawful residential purposes.\n"
                                            "- Maintain the property in good condition and report damages promptly.",
        "general_provisions": (
            "1. The Tenant may not assign this lease or sublet the property, in whole or in part, without the Landlord's prior written consent.\n"
            "2. Breach of any material term by either party entitles the other party to terminate this agreement in accordance with applicable law.\n"
            "3. This agreement shall be governed by the laws applicable in the property's jurisdiction.\n"
            "4. Any dispute arising from this agreement shall first be referred to good-faith negotiation between the parties before other remedies are pursued."
        ),
        "is_fallback": True,
    }


def generate_agreement_content(listing, poster, tenant) -> dict:
    """
    Sends listing/poster/tenant data to Gemini and returns a structured
    agreement dict. On any failure (missing key, timeout, API error,
    malformed response, quota exceeded), returns a deterministic
    template-based fallback dict instead of raising — callers can check
    `is_fallback` to show a badge / offer a later retry.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return _fallback_result(listing, "GEMINI_API_KEY is not configured")

    try:
        client = genai.Client(api_key=api_key)

        prompt = f"""
        You are an expert legal drafting assistant for NestMatch, a roommate/room-rental
        platform. Draft a clear, formal rental (lease) agreement in the style of a
        professional legal contract, between a Landlord and a Tenant, based strictly on
        the facts given below. Do not invent facts not provided — in particular, no
        specific deposit amount is tracked by the system: if security_deposit_required is
        true, state that a deposit is required "as agreed upon separately between the
        parties" rather than naming a figure; if false, omit deposit language entirely.

        Landlord:
        {_build_poster_data(poster)}

        Tenant:
        {_build_tenant_data(tenant)}

        Property and terms:
        {_build_listing_data(listing)}

        Write in formal contract language ("the Landlord", "the Tenant", "shall"), organized
        into the six clauses defined by the schema. For landlord_obligations, tenant_obligations,
        and general_provisions, produce a plain-text list with one item per line prefixed by
        "- " (obligations) or a number like "1. " (general provisions) — no markdown symbols
        (no **, no #). Tenant obligations should incorporate the property's house rules as
        specific obligations, not just restate them as a bare list. Do not include a
        signature block or witness section — that is handled separately by the document template.

        IMPORTANT LENGTH LIMIT: this entire document must fit on at most 2 printed pages, so be
        concise everywhere. Each of subject_of_lease, term_and_duration, and rent_and_payment_terms
        must be at most 2-3 short sentences. Group related house rules into combined obligations
        rather than listing each separately (e.g. combine all smoking/alcohol/pet restrictions into
        one item) — landlord_obligations must have at most 4 items, tenant_obligations at most 6
        items (grouped, even if many house rules are set), and general_provisions at most 4 items.
        Each list item must be one short sentence.
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": AgreementSchema,
                "temperature": 0.2,
            },
        )

        result: AgreementSchema = response.parsed
        data = result.model_dump()
        data["is_fallback"] = False
        return data

    except Exception as e:
        logger.exception("Error generating agreement via Gemini API: %s", e)
        return _fallback_result(listing, str(e))
