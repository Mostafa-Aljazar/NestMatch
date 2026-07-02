from django.urls import path
from . import views

app_name = 'accounts_app'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_page_view, name='register_page'),
    path('register/create/', views.register_create_view, name='register_create'),

    # Profile page (GET) — shows the user's data across all tabs
    path('profile/', views.profile_view, name='profile'),

    # Separate POST-only endpoints, one per form on the profile page.
    # Keeping these independent means a validation error in the lifestyle
    # form never touches/overwrites the personal info data, and vice versa.
    path('profile/update/personal-info/', views.profile_update_personal_info, name='profile_update_personal_info'),
    path('profile/update/lifestyle/', views.profile_update_lifestyle, name='profile_update_lifestyle'),
    path('profile/review/submit/', views.submit_review, name='submit_review'),
    path('profile/review/<int:review_id>/delete/', views.delete_review, name='delete_review'),
    path('profile/update/password/', views.change_password_view, name='change_password'),

    #OTP
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    path('reset-password/', views.reset_password_view, name='reset_password'),

    
    #verification
    path('verification/', views.verification_view, name='verification'),
    path('verification/document/<int:doc_id>/', views.serve_verification_document, name='verification_document'),

    path('logout/', views.logout_view, name='logout'),
    path('delete-account/', views.delete_account_view, name='delete_account'),
]
