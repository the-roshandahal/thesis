from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('', views.homepage, name='homepage'),
    path('notifications/', views.view_all_notifications, name='view_all_notifications'),
    path('notification/read/<int:notification_id>/', views.mark_notification_as_read_and_redirect, name='mark_notification_as_read_and_redirect'),
    path('notifications/mark_all_as_read/', views.mark_all_notifications_as_read, name='mark_all_notifications_as_read'),


]