from django.urls import path
from . import views

app_name = 'applications_app'

urlpatterns = [
    path('', views.index, name='index'),
]
