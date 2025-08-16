from django.db import models
from django.contrib.auth.models import AbstractUser
from accounts.models import *
from django.utils import timezone


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
    last_modified = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.title
    
    @property
    def is_available_for_application(self):
        """
        Check if the project is actually available for new applications.
        A project is available if:
        1. The availability field is 'available'
        2. It doesn't have any accepted applications
        3. Projects with only 'applied' or 'declined' applications are still available
        """
        # Debug: Print the current availability field value
        print(f"DEBUG: Project '{self.title}' - availability field: '{self.availability}'")
        
        if self.availability != 'available':
            print(f"DEBUG: Project '{self.title}' - availability field is not 'available', returning False")
            return False
        
        # Debug: Check applications count and status
        all_applications = self.applications.all()
        accepted_applications = self.applications.filter(status='accepted')
        applied_applications = self.applications.filter(status='applied')
        declined_applications = self.applications.filter(status='declined')
        
        print(f"DEBUG: Project '{self.title}' - Total applications: {all_applications.count()}")
        print(f"DEBUG: Project '{self.title}' - Accepted applications: {accepted_applications.count()}")
        print(f"DEBUG: Project '{self.title}' - Applied applications: {applied_applications.count()}")
        print(f"DEBUG: Project '{self.title}' - Declined applications: {declined_applications.count()}")
        
        # Check if there are any accepted applications
        has_accepted = accepted_applications.exists()
        print(f"DEBUG: Project '{self.title}' - Has accepted applications: {has_accepted}")
        
        # Project is available if there are NO accepted applications
        # Even if there are 'applied' or 'declined' applications, it's still available
        is_available = not has_accepted
        print(f"DEBUG: Project '{self.title}' - Is available: {is_available}")
        
        if is_available and all_applications.exists():
            print(f"DEBUG: Project '{self.title}' - Available despite having {all_applications.count()} applications (all are 'applied' or 'declined')")
        
        return is_available
    
    def update_availability_status(self):
        """
        Update the availability status based on current applications.
        This should be called when application statuses change.
        
        Rules:
        - Project is 'taken' ONLY when there is at least one 'accepted' application
        - Project is 'available' when there are no 'accepted' applications
        - Projects with only 'applied' or 'declined' applications remain 'available'
        """
        print(f"DEBUG: update_availability_status called for project '{self.title}'")
        print(f"DEBUG: Current availability field: {self.availability}")
        
        # Check all applications for this project
        all_applications = self.applications.all()
        accepted_applications = self.applications.filter(status='accepted')
        
        print(f"DEBUG: Total applications found: {all_applications.count()}")
        print(f"DEBUG: Accepted applications found: {accepted_applications.count()}")
        
        # List all applications and their statuses
        for app in all_applications:
            print(f"DEBUG: Application {app.id}: status='{app.status}', project='{app.project.title}'")
        
        accepted_count = accepted_applications.count()
        
        if accepted_count > 0:
            # At least one application is accepted - project is taken
            if self.availability != 'taken':
                print(f"DEBUG: Updating project '{self.title}' availability from '{self.availability}' to 'taken' (has {accepted_count} accepted applications)")
                self.availability = 'taken'
        else:
            # No accepted applications - project is available
            if self.availability != 'available':
                print(f"DEBUG: Updating project '{self.title}' availability from '{self.availability}' to 'available' (no accepted applications)")
                self.availability = 'available'
        
        print(f"DEBUG: Final availability after update: {self.availability}")
        self.save()


class ProjectArea(models.Model):
    project = models.ForeignKey(Project, related_name='areas', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name



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
