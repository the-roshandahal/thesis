from django.urls import path
from . import views


urlpatterns = [
    # Dashboard view
    path('grading', views.grading_dashboard, name='grading'),
    
    # Project submissions
    path('projects/<int:project_id>/', views.view_project_submissions, name='project_submissions'),
    
    # Grade submission
    path('submissions/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),
    
    # Submission files (for modal)
    path('submissions/<int:submission_id>/files/', views.submission_files, name='submission_files'),
]