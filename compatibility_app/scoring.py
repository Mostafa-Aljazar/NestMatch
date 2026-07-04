from .models import CompatibilityScore
from .utils import calculate_room_compatibility


def get_or_compute_score(seeker, profile, listing):
    """
    Returns the cached (or freshly computed) CompatibilityScore row, or None
    if `profile` is None (seeker hasn't completed onboarding — never fabricate
    a score for that case).
    """
    if profile is None:
        return None

    cached = CompatibilityScore.objects.filter(seeker=seeker, listing=listing).first()
    if cached and cached.profile_updated_at == profile.updated_at and cached.listing_updated_at == listing.updated_at:
        return cached

    data = calculate_room_compatibility(profile, listing)
    return CompatibilityScore.objects.update_or_create(
        seeker=seeker, listing=listing,
        defaults={
            'overall_score': data['overall_score'],
            'sleep_schedule_match': data['sleep_schedule_match'],
            'cleanliness_match': data['cleanliness_match'],
            'noise_match': data['noise_match'],
            'breakdown_summary': data['breakdown_summary'],
            'is_fallback': data['is_fallback'],
            'profile_updated_at': profile.updated_at,
            'listing_updated_at': listing.updated_at,
        },
    )[0]


def get_or_compute_scores_bulk(seeker, profile, listings):
    """
    Batch version for the listings page — one query to pull existing cache
    rows for (seeker, these listings), only calls Gemini for pairs that are
    missing or stale, avoids N+1 cache lookups.
    """
    if profile is None:
        return {}

    listings = list(listings)
    existing = {
        row.listing_id: row
        for row in CompatibilityScore.objects.filter(seeker=seeker, listing__in=listings)
    }

    result = {}
    for listing in listings:
        cached = existing.get(listing.pk)
        if cached and cached.profile_updated_at == profile.updated_at and cached.listing_updated_at == listing.updated_at:
            result[listing.pk] = cached
        else:
            result[listing.pk] = get_or_compute_score(seeker, profile, listing)
    return result
