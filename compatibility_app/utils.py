import os
import logging
from google import genai
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CompatibilitySchema(BaseModel):
    overall_score: int = Field(description="A weighted compatibility score from 0 to 100 based on lifestyle factors.")
    sleep_schedule_match: int = Field(description="0 to 100 score for how well the seeker's sleep/wake schedule fits this room's noise/quiet-hours rules.")
    cleanliness_match: int = Field(description="0 to 100 score for matching cleanliness expectations.")
    noise_match: int = Field(description="0 to 100 score for matching noise tolerance with this room's noise-related house rules.")
    breakdown_summary: str = Field(description="A brief 2-3 sentence overview explaining why they match or mismatch.")


def _build_seeker_data(profile) -> dict:
    # All LifestyleProfile fields are required except wake_time/religion/field
    # (see accounts_app.LifestyleProfile.lifestyle_validator) — every seeker
    # gives Gemini the full 22-field picture, not a partial one.
    return {
        "sleep_time": profile.get_sleep_time_display(),
        "wake_time": profile.get_wake_time_display() if profile.wake_time else None,
        "noise_level": profile.get_noise_level_display(),
        "cleanliness": profile.get_cleanliness_display(),
        "cooking": profile.cooking,
        "pets": profile.pets,
        "smoking": profile.get_smoking_display(),
        "social_type": profile.get_social_type_display(),
        "preferred_roommates": profile.get_preferred_roommates_display(),
        "religion": profile.get_religion_display() if profile.religion else None,
        "roommate_gender_pref": profile.get_roommate_gender_pref_display(),
        "budget_min": profile.budget_min,
        "budget_max": profile.budget_max,
        "dietary": profile.get_dietary_display(),
        "guest_tolerance": profile.get_guest_tolerance_display(),
        "tenant_type": profile.get_tenant_type_display(),
        "household_lang_pref": profile.get_household_lang_pref_display(),
        "alcohol_ok": profile.alcohol_ok,
        "min_stay_pref": profile.get_min_stay_pref_display(),
        "listing_type_pref": profile.get_listing_type_pref_display(),
        "works_from_home": profile.works_from_home,
        "wants_furnished": profile.wants_furnished,
        "wants_building_amenities": profile.wants_building_amenities,
    }


def _build_listing_data(listing) -> dict:
    # Boolean/attribute groups that map onto LifestyleProfile categories —
    # not the full ~100-field house-rule set (keeps the prompt small/cheap
    # and avoids sending irrelevant fields like security/parking/laundry).
    return {
        "smoking_rules": {
            "no_smoking": listing.no_smoking, "smoking_outside_ok": listing.smoking_outside_ok,
            "no_alcohol": listing.no_alcohol, "no_vaping": listing.no_vaping,
        },
        "pet_rules": {
            "pets_allowed": listing.pets_allowed, "dogs_allowed": listing.dogs_allowed,
            "cats_allowed": listing.cats_allowed, "no_pets": listing.no_pets,
        },
        "cleanliness_rules": {
            "shared_cleaning": listing.shared_cleaning, "no_shoes_inside": listing.no_shoes_inside,
            "respect_spaces": listing.respect_spaces, "clean_bathroom": listing.clean_bathroom,
            "separate_recycling": listing.separate_recycling,
        },
        "noise_rules": {
            "quiet_after_10": listing.quiet_after_10, "early_sleepers": listing.early_sleepers,
            "no_loud_music": listing.no_loud_music, "no_parties": listing.no_parties,
            "calm_environment": listing.calm_environment, "no_calls_common": listing.no_calls_common,
        },
        "religion_rules": {
            "muslims_only": listing.muslims_only, "christians_only": listing.christians_only,
            "all_religions_ok": listing.all_religions_ok, "halal_kitchen": listing.halal_kitchen,
            "prayer_space": listing.prayer_space,
        },
        "gender_rules": {"males_only": listing.males_only, "females_only": listing.females_only},
        "tenant_rules": {
            "students_only": listing.students_only, "professionals_only": listing.professionals_only,
            "expats_welcome": listing.expats_welcome, "no_children": listing.no_children,
        },
        "kitchen_rules": {
            "must_cook": listing.must_cook, "equipped_kitchen": listing.equipped_kitchen,
            "vegetarian_house": listing.vegetarian_house, "no_seafood": listing.no_seafood,
            "shared_groceries": listing.shared_groceries,
        },
        "guest_rules": {
            "no_overnight_guests": listing.no_overnight_guests, "guests_with_notice": listing.guests_with_notice,
        },
        "amenities": {"fully_furnished": listing.fully_furnished},
        "listing_type": listing.get_listing_type_display(),
        "price": float(listing.price),
        "min_stay_months": listing.min_stay_months,
        "max_occupants": listing.max_occupants,
    }


def _fallback_result(reason: str) -> dict:
    logger.warning("Gemini compatibility scoring unavailable: %s", reason)
    return {
        "overall_score": 50, "sleep_schedule_match": 50, "cleanliness_match": 50, "noise_match": 50,
        "breakdown_summary": "AI match score temporarily unavailable — showing a neutral placeholder.",
        "is_fallback": True,
    }


def calculate_room_compatibility(seeker_profile, listing) -> dict:
    """
    Sends the seeker's LifestyleProfile and this Listing's house-rule flags
    to Gemini and returns a structured match breakdown as a dict.
    On any failure (missing key, timeout, API error, malformed response),
    returns a neutral fallback dict instead of raising — callers can check
    `is_fallback` to decide whether to retry later.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return _fallback_result("GEMINI_API_KEY is not configured")

    try:
        client = genai.Client(api_key=api_key)

        prompt = f"""
        You are an expert roommate-matching AI for NestMatch. Analyze how compatible
        this room seeker is with the following room listing, based on the seeker's
        lifestyle preferences and the room's stated house rules.

        Seeker's lifestyle preferences:
        {_build_seeker_data(seeker_profile)}

        Room's house rules:
        {_build_listing_data(listing)}

        Evaluate sleep/noise schedule fit, cleanliness expectations, noise tolerance,
        smoking/alcohol/vaping, pets, religion-related house rules, gender and tenant-type
        restrictions, dietary/kitchen fit, guest tolerance, budget/price fit, minimum stay
        fit, and occupancy fit. A room rule that was not set for a category means no
        restriction was stated for that category — treat as neutral, not as an automatic
        mismatch or automatic match. Every seeker preference listed is a stated preference
        (wake_time, religion, and field may be null if the seeker chose not to share them
        — treat those specific nulls as neutral too).
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": CompatibilitySchema,
                "temperature": 0.1,
            },
        )

        result: CompatibilitySchema = response.parsed
        data = result.model_dump()
        data["is_fallback"] = False
        for key in ("overall_score", "sleep_schedule_match", "cleanliness_match", "noise_match"):
            data[key] = max(0, min(100, int(data[key])))
        return data

    except Exception as e:
        logger.exception("Error calculating compatibility via Gemini API: %s", e)
        return _fallback_result(str(e))
