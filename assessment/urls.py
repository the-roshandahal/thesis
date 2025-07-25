from django.urls import path
from . import views

urlpatterns = [
    path('assessment_schema/', views.assessment_schema, name='assessment_schema'),
    path('create_assessment_schema', views.create_assessment_schema, name='create_assessment_schema'),
    path('edit_schema/<int:id>', views.edit_schema, name='edit_schema'),
    path('add_assessment/<int:id>', views.add_assessment, name='add_assessment'),
    path('edit_assessment/<int:id>', views.edit_assessment, name='edit_assessment'),
    path('student_view_assignment', views.student_view_assignment, name='student_view_assignment'),
    path('attempt_assessment/<int:id>', views.attempt_assessment, name='attempt_assessment'),
    path('view_submission/<int:assessment_id>/', views.view_submission, name='view_submission'),
    # Add other URLs if needed
]
