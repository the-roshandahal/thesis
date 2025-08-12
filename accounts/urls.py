from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('student_admin/', views.student_admin, name='student_admin'),
    path('add_student/', views.add_student, name='add_student'),
    path('supervisor_admin/', views.supervisor_admin, name='supervisor_admin'),
    path('add_supervisor/', views.add_supervisor, name='add_supervisor'),
    path('view_profile/', views.view_profile, name='view_profile'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('change-password/', views.change_password, name='change_password'),

]