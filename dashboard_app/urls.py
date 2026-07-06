from django.urls import path
from . import views

app_name = 'dashboard_app'

urlpatterns = [
    # Dashboard pages
    path('', views.index, name='index'),
    path('overview/', views.overview, name='overview'),
    path('users/', views.users_list, name='users'),
    path('listings/', views.listings_list, name='listings'),
    path('banned-users/', views.banned_users_list, name='banned_users'),
    path('messages/', views.messages_list, name='messages'),
    path('applications/', views.applications_list, name='applications'),
    path('verification/', views.verification_list, name='verification'),
    path('reviews/', views.reviews_list, name='reviews'),
    path('site-content/', views.site_content_page, name='site_content'),
    path('settings/', views.settings_page, name='settings'),

    # User moderation
    path('ban/<int:user_id>/', views.ban_user, name='ban_user'),
    path('unban/<int:user_id>/', views.unban_user, name='unban_user'),
    path('user/<int:user_id>/listings/', views.view_user_listings, name='view_user_listings'),
    path('user/<int:user_id>/applications/', views.view_user_applications, name='view_user_applications'),
    path('user/<int:user_id>/delete/', views.delete_user, name='delete_user'),

    # Listing moderation
    path('listing/hide/<int:listing_id>/', views.hide_listing, name='hide_listing'),
    path('listing/restore/<int:listing_id>/', views.restore_listing, name='restore_listing'),
    path('listing/delete/<int:listing_id>/', views.delete_listing, name='delete_listing'),

    # Listing detail (admin — all applications for a room)
    path('listing/<int:listing_id>/', views.listing_detail, name='listing_detail'),

    # Contact messages
    path('messages/read/<int:message_id>/', views.mark_message_read, name='mark_message_read'),
    path('messages/delete/<int:message_id>/', views.delete_message, name='delete_message'),

    # Site content update
    path('site-content/update/', views.update_site_content, name='update_site_content'),

    # Verification
    path('verification/<int:doc_id>/approve/', views.approve_document, name='approve_document'),
    path('verification/<int:doc_id>/reject/', views.reject_document, name='reject_document'),

    # Reviews
    path('reviews/<int:review_id>/approve/', views.approve_review, name='approve_review'),
    path('reviews/<int:review_id>/reject/', views.reject_review, name='reject_review'),
]