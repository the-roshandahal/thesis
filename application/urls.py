from django.urls import path
from . import views

urlpatterns = [
    path('project/<int:project_id>/apply/', views.apply_to_project, name='apply_to_project'),
    path('supervisor_application/', views.supervisor_application, name='supervisor_application'),
    path('application/<int:application_id>/accept/', views.accept_application, name='accept_application'),
    path('application/<int:application_id>/decline/', views.decline_application, name='decline_application'),
]
