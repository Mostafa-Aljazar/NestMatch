from django.urls import path
from . import views

app_name = 'listings_app'

urlpatterns = [
    path('',              views.listings_page,  name='listings'),
    path('new/',          views.post_room_page, name='post_room'),
    path('create/',       views.create_listing, name='create_listing'),
    path('<int:pk>/',     views.room_detail,    name='room_detail'),
]
