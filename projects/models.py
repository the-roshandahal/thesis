from django.db import models
from django.contrib.auth.models import AbstractUser
from accounts.models import *
from django.utils import timezone


# Create your models here.
class Project(models.Model):
    PROJECT_TYPES = [
        ('Research', 'Research'),
        ('Development', 'Development'),
        ('R and D', 'R and D'),
    ]

    title = models.CharField(max_length=255)
    project_type = models.CharField(max_length=50, choices=PROJECT_TYPES)
    prerequisites = models.CharField(max_length=255)
    description = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    supervisor = models.ForeignKey(User, on_delete= models.CASCADE)
    availability = models.CharField(max_length=100, default='available')
    last_modified = models.DateTimeField(default=timezone.now())
    def __str__(self):
        return self.title


class ProjectArea(models.Model):
    project = models.ForeignKey(Project, related_name='areas', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name



# models.py
class ProjectFile(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='project_files/%Y/%m/%d/')  # Organized storage
    display_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']


class ProjectLink(models.Model):
    project = models.ForeignKey(Project, related_name='links', on_delete=models.CASCADE)
    url = models.URLField()

    def __str__(self):
        return self.url
