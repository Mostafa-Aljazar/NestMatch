from django.urls import path
from . import views

app_name = 'applications_app'

urlpatterns = [
    path('', views.my_applications, name='my_applications'),
    path('apply/<int:pk>/', views.apply_to_listing, name='apply'),
    path('withdraw/<int:pk>/', views.withdraw_application, name='withdraw'),

    # Poster-facing: applicants for a listing
    path('listing/<int:pk>/', views.listing_applicants, name='listing_applicants'),
    path('application/<int:pk>/accept/', views.accept_application, name='accept_application'),
    path('application/<int:pk>/reject/', views.reject_application, name='reject_application'),
]
