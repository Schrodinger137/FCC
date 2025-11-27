"""
URL configuration for FCC project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from FightClubCafe import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # GENERAL SECTION
    path('', views.index, name='index'),
    path('characters/', views.characters, name='characters'),
    path('items/', views.items, name='items'),
    path('chat/', views.chat, name='chat'),

    # SESSION SECTION
    path('signin/', views.signin, name='signin'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('account/', views.account, name='account'),

    # ADMIN SECTION
    path('administrator/', views.administrator, name='administrator'),

    # USERS SECTION
    path('admin_users/', views.admin_users, name='admin_users'),
    path('admin/users/create/', views.create_user, name='create_user'),
    path('admin_users/delete/<str:user_id>/', views.delete_user, name='delete_user'),

    # CHARACTER SECTION
    path('admin_characters/', views.admin_characters, name='admin_characters'),
    path('admin_characters/delete/<str:character_id>/', views.delete_character, name='delete_character'),

    # ITEMS SECTION
    path('admin_items/', views.admin_items, name='admin_items'),
    path('admin_items/delete/<str:item_id>/', views.delete_item, name='delete_item'),

    # PWA
    path('', include('pwa.urls')),
]

