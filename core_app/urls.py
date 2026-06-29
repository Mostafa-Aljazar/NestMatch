from django.urls import path
from . import views

app_name = 'core_app'

urlpatterns = [
    path('', views.index, name='index'),
    path('faq/', views.faq, name='faq'),
]
