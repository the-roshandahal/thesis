from django.urls import path
from . import views

urlpatterns = [
    path('project_supervisor/', views.project_supervisor, name='project_supervisor'),
    path('add_project/', views.add_project, name='add_project'),
    path('edit_project/<int:project_id>/', views.edit_project, name='edit_project'),
    path('delete_file/<int:file_id>/', views.delete_file, name='delete_file'),
    path('student_projects/', views.student_projects, name='student_projects'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
]