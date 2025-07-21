from django.db import models
from projects.models import *
from django.conf import settings
from django.utils import timezone

class Application(models.Model):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='applications')
    application_type = models.CharField(max_length=20, choices=[('individual', 'Individual'), ('group', 'Group')])
    status = models.CharField(
        max_length=10,
        choices=[('applied', 'Applied'), ('accepted', 'Accepted'), ('declined', 'Declined')],
        default='applied'
    )
    message = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.application_type.title()} Application - {self.project.title} ({self.status})"


class ApplicationMember(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='application_memberships')
    is_leader = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} - {'Leader' if self.is_leader else 'Member'}"