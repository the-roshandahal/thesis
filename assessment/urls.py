from django.urls import path
from . import views

urlpatterns = [
    path('assessment_schema/', views.assessment_schema, name='assessment_schema'),
    path('create_assessment_schema', views.create_assessment_schema, name='create_assessment_schema'),
    path('edit_schema/<int:id>', views.edit_schema, name='edit_schema'),
    path('add_assessment/<int:id>', views.add_assessment, name='add_assessment'),
    path('edit_assessment/<int:id>', views.edit_assessment, name='edit_assessment'),
    # Add other URLs if needed
]
