from django.urls import path
from . import views

app_name = 'dashboard_app'

urlpatterns = [
    path('', views.index, name='index'),

    # User moderation
    path('ban/<int:user_id>/',   views.ban_user,   name='ban_user'),
    path('unban/<int:user_id>/', views.unban_user, name='unban_user'),

    # Listing moderation
    path('listing/hide/<int:listing_id>/',    views.hide_listing,    name='hide_listing'),
    path('listing/restore/<int:listing_id>/', views.restore_listing, name='restore_listing'),
    path('listing/delete/<int:listing_id>/',  views.delete_listing,  name='delete_listing'),
]