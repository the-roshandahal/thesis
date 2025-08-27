from django.urls import path
from . import views

urlpatterns = [
    path('assessment_schema/', views.assessment_schema, name='assessment_schema'),
    path('create_assessment_schema', views.create_assessment_schema, name='create_assessment_schema'),
    path('edit_schema/<int:id>', views.edit_schema, name='edit_schema'),
    path('add_assessment/<int:id>', views.add_assessment, name='add_assessment'),
    path('edit_assessment/<int:id>', views.edit_assessment, name='edit_assessment'),
    path('delete_assessment/<int:id>/', views.delete_assessment, name='delete_assessment'),
    path('student_view_assignment', views.student_view_assignment, name='student_view_assignment'),
    path('attempt_assessment/<int:id>', views.attempt_assessment, name='attempt_assessment'),
    # path('assessment/view_submission/<int:assessment_id>/', views.view_submission, name='view_submission'),

    # Individual assignments
    path('view_individual/<int:assessment_id>/', views.view_individual_submission, name='view_individual_submission'),

    # Group assignments
    path('view_group/<int:assessment_id>/', views.view_group_submission, name='view_group_submission'),

    # Add other URLs if needed
]
