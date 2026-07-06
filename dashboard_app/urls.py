from django.urls import path
from . import views

app_name = 'dashboard_app'

urlpatterns = [
    path('', views.index, name='index'),

    # User moderation
    path('ban/<int:user_id>/', views.ban_user, name='ban_user'),
    path('unban/<int:user_id>/', views.unban_user, name='unban_user'),

    # Listing moderation
    path('listing/hide/<int:listing_id>/', views.hide_listing, name='hide_listing'),
    path('listing/restore/<int:listing_id>/', views.restore_listing, name='restore_listing'),
    path('listing/delete/<int:listing_id>/', views.delete_listing, name='delete_listing'),

    # Listing detail (admin — all applications for a room)
    path('listing/<int:listing_id>/', views.listing_detail, name='listing_detail'),

    # Contact messages
    path('messages/read/<int:message_id>/', views.mark_message_read, name='mark_message_read'),
    path('messages/delete/<int:message_id>/', views.delete_message, name='delete_message'),

    # Site content
    path('site-content/', views.update_site_content, name='update_site_content'),

    # Verification
    path('verification/<int:doc_id>/approve/', views.approve_document, name='approve_document'),
    path('verification/<int:doc_id>/reject/', views.reject_document, name='reject_document'),

    # Reviews
    path('reviews/<int:review_id>/approve/', views.approve_review, name='approve_review'),
    path('reviews/<int:review_id>/reject/', views.reject_review, name='reject_review'),
]