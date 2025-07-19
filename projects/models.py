from django.db import models
from django.db import models
from django.contrib.auth.models import AbstractUser
from accounts.models import *

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

    def __str__(self):
        return self.title


class ProjectArea(models.Model):
    project = models.ForeignKey(Project, related_name='areas', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class ProjectFile(models.Model):
    project = models.ForeignKey(Project, related_name='files', on_delete=models.CASCADE)
    file = models.FileField(upload_to='project_files/')

    def __str__(self):
        return self.file.name


class ProjectLink(models.Model):
    project = models.ForeignKey(Project, related_name='links', on_delete=models.CASCADE)
    url = models.URLField()

    def __str__(self):
        return self.url
