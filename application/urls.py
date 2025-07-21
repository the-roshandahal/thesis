from django.urls import path
from . import views

urlpatterns = [
    path('project/<int:project_id>/apply/', views.apply_to_project, name='apply_to_project'),

]