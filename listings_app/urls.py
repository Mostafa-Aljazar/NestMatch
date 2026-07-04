from django.urls import path
from . import views

app_name = 'listings_app'

urlpatterns = [
    path('',                 views.listings_page,  name='listings'),
    path('new/',              views.post_room_page, name='post_room'),
    path('create/',           views.create_listing, name='create_listing'),
    path('my-listings/',      views.my_listings,    name='my_listings'),
    path('favorites/',        views.favorites_page, name='favorites'),
    path('<int:pk>/',         views.room_detail,    name='room_detail'),
    path('<int:pk>/edit/',    views.post_room_page, name='edit_room'),
    path('<int:pk>/update/',  views.update_listing, name='update_listing'),
    path('<int:pk>/delete/',  views.delete_listing, name='delete_listing'),
    path('<int:pk>/photos/', views.photo_tour,  name='photo_tour'),
    path('<int:pk>/review/', views.post_review, name='post_review'),
    path('<int:pk>/favorite/', views.toggle_favorite, name='toggle_favorite'),
]
