from django.urls import path
from . import views

app_name = 'applications_app'

urlpatterns = [
    path('', views.my_applications, name='my_applications'),
    path('apply/<int:pk>/', views.apply_to_listing, name='apply'),
    path('withdraw/<int:pk>/', views.withdraw_application, name='withdraw'),
]
