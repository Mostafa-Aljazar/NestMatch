from django.urls import path
from . import views

app_name = 'agreements_app'

urlpatterns = [
    path('', views.index, name='index'),
]
