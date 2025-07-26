from django.urls import path
from . import views

urlpatterns = [
    path('project_supervisor/', views.project_supervisor, name='project_supervisor'),
    path('add_project/', views.add_project, name='add_project'),
    path('student_projects/', views.student_projects, name='student_projects'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
]