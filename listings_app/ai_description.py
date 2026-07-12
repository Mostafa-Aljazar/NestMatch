import json
import logging
import os

from google import genai

logger = logging.getLogger(__name__)


def _normalize_text(value) -> str:
    return str(value).strip() if value is not None else ''


def _normalize_custom_requirements(data: dict) -> list[str]:
    raw_value = data.get('custom_requirements', [])
    if isinstance(raw_value, str):
        raw_value = raw_value.strip()
        if not raw_value:
            return []
        try:
            raw_value = json.loads(raw_value)
        except json.JSONDecodeError:
            raw_value = [raw_value]

    if isinstance(raw_value, dict):
        raw_value = [raw_value]

    items: list[str] = []
    for item in raw_value or []:
        if isinstance(item, dict):
            text = item.get('text') or item.get('value') or item.get('title') or item.get('label') or ''
        else:
            text = str(item)
        text = _normalize_text(text)
        if text:
            items.append(text)
    return items


def _build_structured_fallback(data: dict) -> str:
    type_map = {
        'private_room': 'a private room in a shared apartment',
        'full_apartment': 'a full apartment',
        'shared_bed': 'a shared room/bed',
        'roommate_wanted': 'a spot for a roommate in an existing household',
    }
    type_desc = type_map.get(_normalize_text(data.get('listing_type')), 'a room')
    title = _normalize_text(data.get('title')) or 'This listing'
    location_parts = [
        _normalize_text(data.get('district')),
        _normalize_text(data.get('city')),
        _normalize_text(data.get('country')),
    ]
    location = ', '.join([part for part in location_parts if part])
    price = _normalize_text(data.get('price')) or 'price not specified'
    tenant_types = _normalize_text(data.get('tenant_types')) or 'anyone'

    requirements = [
        req.strip()
        for req in _normalize_text(data.get('requirements')).split(',')
        if req.strip()
    ]
    requirements.extend(_normalize_custom_requirements(data))

    location_sentence = f"It is located in {location}." if location else 'The location details are still being finalized.'
    price_sentence = f"The monthly rent is {price}."
    tenant_sentence = f"It is a good fit for {tenant_types}."

    if requirements:
        rules_sentence = 'Key preferences and house notes: ' + '; '.join(requirements[:6]) + '.'
    else:
        rules_sentence = 'No specific requirements were added.'

    return (
        f"{title} offers {type_desc}. {location_sentence}\n\n"
        f"{price_sentence} {tenant_sentence}\n\n"
        f"{rules_sentence}"
    )


def generate_listing_description(data: dict) -> str | None:
    """
    Generates a listing description via Gemini based on listing data.
    If Gemini is unavailable or fails, it gracefully falls back to a neat,
    structured description that reflects the information the user actually provided.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("Gemini description generation unavailable: GEMINI_API_KEY is not configured")
        return _build_structured_fallback(data)

    type_map = {
        'private_room': 'a private room in a shared apartment',
        'full_apartment': 'a full apartment',
        'shared_bed': 'a shared room/bed',
        'roommate_wanted': 'a spot for a roommate in an existing household',
    }
    type_desc = type_map.get(_normalize_text(data.get('listing_type')), 'a room')
    custom_requirements = _normalize_custom_requirements(data)
    requirements_text = _normalize_text(data.get('requirements'))
    if custom_requirements:
        requirements_text = requirements_text + ('; ' + '; '.join(custom_requirements) if requirements_text else '; '.join(custom_requirements))

    prompt = f"""Write a warm, polished listing description in English for a roommate-matching platform.

Use only the facts provided below. Do not invent amenities, landmarks, or distances.
Output 3 short paragraphs separated by blank lines. Keep it honest, practical, and welcoming.

Details:
- Type: {type_desc}
- Title: {_normalize_text(data.get('title')) or 'not provided'}
- Location: {', '.join(part for part in [
    _normalize_text(data.get('district')),
    _normalize_text(data.get('city')),
    _normalize_text(data.get('country')),
] if part)}
- Monthly rent: {_normalize_text(data.get('price')) or 'not specified'}
- Who it's for: {_normalize_text(data.get('tenant_types')) or 'anyone'}
- Key features/rules: {requirements_text or 'none specified'}

Rules:
- Mention the title, place, price, and the intended tenant type clearly.
- Preserve the user-entered requirements in a neat, ordered way.
- No markdown, no headings, no bullet points, no extra invented details.
- Keep the total length under 120 words."""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"temperature": 0.3},
        )
        text = (response.text or "").strip()
        return text or _build_structured_fallback(data)
    except Exception as e:
        logger.exception("Error generating listing description via Gemini API: %s", e)
        return _build_structured_fallback(data)