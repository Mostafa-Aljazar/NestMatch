import io
import logging
import re

from django.core.files.base import ContentFile
from django.template.loader import render_to_string

from .models import Agreement
from .utils import generate_agreement_content

logger = logging.getLogger(__name__)

PARAGRAPH_CLAUSES = [
    ('subject_of_lease', 'CLAUSE 1 — SUBJECT OF LEASE'),
    ('term_and_duration', 'CLAUSE 2 — TERM AND DURATION'),
    ('rent_and_payment_terms', 'CLAUSE 3 — RENT AND PAYMENT TERMS'),
]
LIST_CLAUSES = [
    ('landlord_obligations', 'CLAUSE 4 — OBLIGATIONS OF THE LANDLORD'),
    ('tenant_obligations', 'CLAUSE 5 — OBLIGATIONS OF THE TENANT'),
    ('general_provisions', 'CLAUSE 6 — GENERAL PROVISIONS'),
]


def get_or_create_agreement(application):
    """
    Returns the existing Agreement for this application if one exists,
    otherwise generates one via Gemini (or fallback) and creates it,
    including its rendered PDF. Never regenerates an existing agreement
    implicitly — see `regenerate_agreement` for the explicit path.
    """
    existing = getattr(application, 'agreement', None)
    if existing is not None:
        return existing

    return _create_agreement(application, version=1)


def regenerate_agreement(application):
    """Explicit action: overwrite the existing agreement with a freshly
    generated one, bumping `version`."""
    existing = getattr(application, 'agreement', None)
    next_version = (existing.version + 1) if existing else 1
    if existing is not None:
        existing.delete()
    return _create_agreement(application, version=next_version)


def _create_agreement(application, version):
    listing = application.listing
    poster = listing.poster
    tenant = application.seeker

    data = generate_agreement_content(listing, poster, tenant)
    list_lines = {key: _split_list_lines(data[key]) for key, _ in LIST_CLAUSES}

    agreement = Agreement.objects.create(
        application=application,
        listing=listing,
        poster=poster,
        tenant=tenant,
        generated_text=_flatten_sections(data, list_lines),
        is_fallback=data['is_fallback'],
        version=version,
    )

    try:
        pdf_bytes = _render_pdf(agreement, data, list_lines)
        agreement.pdf_file.save(f'agreement_{agreement.pk}.pdf', ContentFile(pdf_bytes), save=True)
    except Exception:
        logger.exception("Failed to render PDF for agreement %s — text saved without a PDF", agreement.pk)

    return agreement


def _flatten_sections(data: dict, list_lines: dict) -> str:
    parts = []
    for key, title in PARAGRAPH_CLAUSES:
        parts.append(f"{title}\n{data[key]}")
    for key, title in LIST_CLAUSES:
        body = "\n".join(f"- {line}" for line in list_lines[key])
        parts.append(f"{title}\n{body}")
    return "\n\n".join(parts)


_LIST_ITEM_RE = re.compile(r'(?:^|(?<=[.\n]))\s*(?:-\s+|\d+\.\s+)')


def _split_list_lines(text: str) -> list:
    """Splits Gemini's "- item- item" / "1. item2. item" style text into a
    clean list of item strings. Gemini doesn't reliably insert a real newline
    between list items despite being asked to — bullet/number markers often
    appear immediately after the prior item's closing period with no line
    break, and sometimes Gemini emits the literal two-character escape
    sequence "\\n" as text rather than an actual newline (normalized away
    first below) — so this splits right after a period (or at the very
    start) when followed by a bullet/number marker, rather than relying
    solely on line breaks."""
    text = text.replace('\\n', '\n').replace('\\r', '')
    items = _LIST_ITEM_RE.split(text)
    return [item.strip() for item in items if item.strip()]


ALL_CLAUSES = PARAGRAPH_CLAUSES + LIST_CLAUSES
_CLAUSE_TITLE_TO_KEY = {title: key for key, title in ALL_CLAUSES}
_CLAUSE_SPLIT_RE = re.compile(
    r'(?:^|\n\n)(' + '|'.join(re.escape(title) for _, title in ALL_CLAUSES) + r')\n'
)


def parse_clauses(generated_text: str) -> dict:
    """
    Splits an Agreement's flattened `generated_text` back into a
    {clause_key: body} dict, keyed the same as `generate_agreement_content`'s
    output, for templates (e.g. the HTML preview page) that want to render
    each clause in its own styled box rather than one plain text blob.
    List-type clauses (landlord/tenant obligations, general provisions) are
    additionally split into a {clause_key + '_lines': [...]} list.
    """
    parts = _CLAUSE_SPLIT_RE.split(generated_text)
    clauses = {}
    for i in range(1, len(parts), 2):
        title = parts[i]
        body = parts[i + 1].strip() if i + 1 < len(parts) else ''
        key = _CLAUSE_TITLE_TO_KEY.get(title)
        if key:
            clauses[key] = body

    for key, _ in LIST_CLAUSES:
        clauses[f'{key}_lines'] = [
            line.lstrip('-').strip() for line in clauses.get(key, '').splitlines() if line.strip()
        ]

    return clauses


def _render_pdf(agreement, data: dict, list_lines: dict) -> bytes:
    pdf_context = dict(data)
    pdf_context['landlord_obligations_lines'] = list_lines['landlord_obligations']
    pdf_context['tenant_obligations_lines'] = list_lines['tenant_obligations']
    pdf_context['general_provisions_lines'] = list_lines['general_provisions']
    return _render_pdf_from_sections(agreement, pdf_context)


def rerender_pdf(agreement):
    """
    Re-renders and re-saves an existing Agreement's PDF from its already-
    stored `generated_text` (via `parse_clauses`), without calling Gemini
    again. Used after a party signs, so the downloadable PDF picks up the
    newly recorded signature without needing a full regenerate.
    """
    sections = parse_clauses(agreement.generated_text)
    pdf_bytes = _render_pdf_from_sections(agreement, sections)
    agreement.pdf_file.save(f'agreement_{agreement.pk}.pdf', ContentFile(pdf_bytes), save=True)


def _render_pdf_from_sections(agreement, sections: dict) -> bytes:
    from xhtml2pdf import pisa

    html = render_to_string('agreements_app/agreement_pdf.html', {
        'agreement': agreement,
        'sections': sections,
    })
    buffer = io.BytesIO()
    pisa.CreatePDF(html, dest=buffer)
    return buffer.getvalue()
