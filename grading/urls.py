from django.urls import path
from . import views

app_name = 'grading'

urlpatterns = [
    path('grading', views.assessment_list, name='grading'),

    # path('', views.assessment_list, name='assessment_list'),
    path('assessments/<int:assessment_id>/', views.assessment_detail, name='assessment_detail'),
    path('submissions/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),
    path('submissions/<int:submission_id>/files/', views.submission_files, name='submission_files'),
    path('publish_grade/<int:assessment_id>/', views.publish_grades, name='publish_grades'),
]