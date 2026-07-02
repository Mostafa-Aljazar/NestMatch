from django.contrib import admin
from django.utils import timezone

from .models import VerificationDocument


@admin.register(VerificationDocument)
class VerificationDocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'document_type', 'status', 'reviewed_by', 'updated_at')
    list_filter = ('status', 'document_type')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_documents', 'reject_documents']

    @admin.action(description='Approve selected documents')
    def approve_documents(self, request, queryset):
        for document in queryset:
            document.approve(reviewer=request.user)
        self.message_user(request, f'{queryset.count()} document(s) approved.')

    @admin.action(description='Reject selected documents (generic reason)')
    def reject_documents(self, request, queryset):
        # For a specific reason per document, open the document and reject it
        # individually from the change form instead — see save_model below.
        for document in queryset:
            document.reject(
                reviewer=request.user,
                reason='Rejected — please contact support for details.',
            )
        self.message_user(request, f'{queryset.count()} document(s) rejected.')

    def save_model(self, request, obj, form, change):
        """
        If an admin manually edits a single document's status from the
        change form (and types a custom rejection_reason there), stamp
        reviewed_by/reviewed_at automatically instead of requiring them
        to set it by hand.
        """
        if change and 'status' in form.changed_data and obj.status in (
            VerificationDocument.APPROVED, VerificationDocument.REJECTED
        ):
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)