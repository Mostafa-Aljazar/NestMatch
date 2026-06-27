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
    path('profile/update/password/', views.change_password_view, name='change_password'),
    path('delete-account/', views.delete_account_view, name='delete_account'),
    # path(
    #     'password-reset/',
    #     auth_views.PasswordResetView.as_view(
    #         template_name='password_reset.html',
    #         email_template_name='password_reset_email.html',
    #         subject_template_name='password_reset_subject.txt',
    #         success_url=reverse_lazy('accounts_app:password_reset_done'),
    #     ),
    #     name='password_reset',
    # ),
    # path(
    #     'password-reset/done/',
    #     auth_views.PasswordResetDoneView.as_view(
    #         template_name='password_reset_done.html',
    #     ),
    #     name='password_reset_done',
    # ),
    # path(
    #     'password-reset/<uidb64>/<token>/',
    #     auth_views.PasswordResetConfirmView.as_view(
    #         template_name='password_reset_confirm.html',
    #         success_url=reverse_lazy('accounts_app:password_reset_complete'),
    #     ),
    #     name='password_reset_confirm',
    # ),
    # path(
    #     'password-reset/complete/',
    #     auth_views.PasswordResetCompleteView.as_view(
    #         template_name='password_reset_complete.html',
    #     ),
    #     name='password_reset_complete',
    # ),
    path('logout/', views.logout_view, name='logout'),

]
