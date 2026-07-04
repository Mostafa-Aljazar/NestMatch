import logging

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden, FileResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from applications_app.models import Application
from .models import Agreement
from .service import get_or_create_agreement, regenerate_agreement, parse_clauses, rerender_pdf

logger = logging.getLogger(__name__)


def _can_access(user, application):
    return user.is_authenticated and (user.id == application.seeker_id or user.id == application.listing.poster_id)


@login_required
@require_POST
def generate_agreement(request, application_pk):
    """POST /agreements/application/<pk>/generate/ — either party may trigger this
    once the application is accepted."""
    application = get_object_or_404(Application, pk=application_pk)
    if not _can_access(request.user, application):
        return JsonResponse({'error': 'Not authorized'}, status=403)
    if application.status != Application.STATUS_ACCEPTED:
        return JsonResponse({'error': 'Agreement can only be generated for accepted applications'}, status=400)

    agreement = get_or_create_agreement(application)
    return JsonResponse({
        'ok': True,
        'agreement_id': agreement.pk,
        'is_fallback': agreement.is_fallback,
        'download_url': f'/agreements/{agreement.pk}/download/',
        'view_url': f'/agreements/{agreement.pk}/view/',
    })


@login_required
@require_POST
def regenerate(request, agreement_pk):
    """POST /agreements/<pk>/regenerate/ — explicit re-draft, poster only."""
    agreement = get_object_or_404(Agreement, pk=agreement_pk)
    if request.user.id != agreement.poster_id:
        return JsonResponse({'error': 'Only the poster can regenerate this agreement'}, status=403)
    if agreement.is_fully_signed:
        return JsonResponse({'error': 'This agreement has been signed by both parties and can no longer be regenerated'}, status=400)

    new_agreement = regenerate_agreement(agreement.application)
    return JsonResponse({
        'ok': True,
        'agreement_id': new_agreement.pk,
        'is_fallback': new_agreement.is_fallback,
        'download_url': f'/agreements/{new_agreement.pk}/download/',
        'view_url': f'/agreements/{new_agreement.pk}/view/',
    })


@login_required
@require_POST
def sign_agreement(request, agreement_pk):
    """POST /agreements/<pk>/sign/ — records the requesting party's typed-name
    signature. A party can only sign for themselves, never on the other's behalf."""
    agreement = get_object_or_404(Agreement, pk=agreement_pk)
    if not _can_access(request.user, agreement.application):
        return JsonResponse({'error': 'Not authorized'}, status=403)

    typed_name = request.POST.get('typed_name', '').strip()
    if not typed_name:
        return JsonResponse({'error': 'Please type your full name to sign'}, status=400)

    if request.user.id == agreement.poster_id:
        agreement.poster_signed_name = typed_name
        agreement.poster_signed_at = timezone.now()
        agreement.save(update_fields=['poster_signed_name', 'poster_signed_at'])
    elif request.user.id == agreement.tenant_id:
        agreement.tenant_signed_name = typed_name
        agreement.tenant_signed_at = timezone.now()
        agreement.save(update_fields=['tenant_signed_name', 'tenant_signed_at'])

    try:
        rerender_pdf(agreement)
    except Exception:
        logger.exception("Failed to re-render PDF for agreement %s after signing", agreement.pk)

    return JsonResponse({'ok': True, 'is_fully_signed': agreement.is_fully_signed})


@login_required
def view_agreement(request, agreement_pk):
    """GET /agreements/<pk>/view/ — HTML preview page."""
    agreement = get_object_or_404(Agreement, pk=agreement_pk)
    if not _can_access(request.user, agreement.application):
        return HttpResponseForbidden("You don't have access to this agreement.")
    return render(request, 'agreements_app/agreement_detail.html', {
        'agreement': agreement,
        'sections': parse_clauses(agreement.generated_text),
    })


@login_required
def download_agreement(request, agreement_pk):
    """GET /agreements/<pk>/download/ — streams the PDF as attachment."""
    agreement = get_object_or_404(Agreement, pk=agreement_pk)
    if not _can_access(request.user, agreement.application):
        return HttpResponseForbidden("You don't have access to this agreement.")

    if not agreement.pdf_file:
        raise Http404("PDF not available — please ask the poster to regenerate the agreement.")

    filename = f'rental_agreement_{agreement.listing.title[:30]}_{agreement.tenant.username}.pdf'.replace(' ', '_')
    return FileResponse(agreement.pdf_file.open('rb'), as_attachment=True, filename=filename)


@login_required
def my_agreements(request):
    """GET /agreements/ — list of agreements the user is party to (either side)."""
    agreements = (
        Agreement.objects
        .filter(Q(poster=request.user) | Q(tenant=request.user))
        .select_related('listing', 'poster', 'tenant')
        .order_by('-created_at')
    )
    return render(request, 'agreements_app/my_agreements.html', {'agreements': agreements})
