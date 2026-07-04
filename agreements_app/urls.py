from django.urls import path
from . import views

app_name = 'agreements_app'

urlpatterns = [
    path('', views.my_agreements, name='my_agreements'),
    path('application/<int:application_pk>/generate/', views.generate_agreement, name='generate'),
    path('<int:agreement_pk>/regenerate/', views.regenerate, name='regenerate'),
    path('<int:agreement_pk>/sign/', views.sign_agreement, name='sign'),
    path('<int:agreement_pk>/view/', views.view_agreement, name='view'),
    path('<int:agreement_pk>/download/', views.download_agreement, name='download'),
]
