from django.urls import path

from .views import (
    post_list, post_detail, create_post,
    update_post, delete_post, register,
    profile_view, home_view, logout_view,
    posts_by_tag, post_list_fragment,
    settings_view,
)

urlpatterns = [
    path('', home_view, name='home'),
    path('posts/', post_list, name='post_list'),
    path('posts/fragment/', post_list_fragment, name='post_list_fragment'),
    path('<int:pk>post_detail/', post_detail, name='post_detail'),
    path('create/', create_post, name='create_post'),
    path('<int:pk>/edit/', update_post, name='post_edit'),
    path('<int:pk>/delete/', delete_post, name='delete_post'),
    path('register/', register, name='register'),
    path('accounts/profile/', profile_view, name='profile'),
    path('logout/', logout_view, name='logout'),
    path('tag/<slug:slug>/', posts_by_tag, name='posts_by_tag'),
    path('settings/', settings_view, name='settings'),

]