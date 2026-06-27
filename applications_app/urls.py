from django.urls import path
from . import views

app_name = 'applications_app'

urlpatterns = [
    path('', views.my_applications, name='my_applications'),
    path('withdraw/<int:pk>/', views.withdraw_application, name='withdraw'),
]
