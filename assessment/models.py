
from django.conf import settings
from django.db import models
from projects.models import *
class AssessmentSchema(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Assessment(models.Model):
    schema = models.ForeignKey(AssessmentSchema, on_delete=models.CASCADE, related_name='assessments')
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    weight = models.PositiveIntegerField(help_text="Percentage weight for this assessment")
    due_date = models.DateField()

    def __str__(self):
        return f"{self.title} ({self.weight}%)"


def assignment_detail_upload_path(instance, filename):
    return f"assessment_details/schema_{instance.assessment.schema.id}/assessment_{instance.assessment.id}/details/{filename}"


def sample_file_upload_path(instance, filename):
    return f"assessment_samples/schema_{instance.assessment.schema.id}/assessment_{instance.assessment.id}/samples/{filename}"

class AssessmentDetailFile(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='detail_files')
    name = models.CharField(max_length=255, help_text="Descriptive name for this file (e.g., 'Assignment Guidelines')")
    file = models.FileField(upload_to=assignment_detail_upload_path)

    def __str__(self):
        return self.name


class AssessmentSampleFile(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='sample_files')
    name = models.CharField(max_length=255, help_text="Descriptive name for this file (e.g., 'Sample Report')")
    file = models.FileField(upload_to=sample_file_upload_path)

    def __str__(self):
        return self.name




def submission_upload_path(instance, filename):
    return f"submissions/user_{instance.student.id}/assessment_{instance.assessment.id}/{filename}"

from django.db import models
from django.utils import timezone

class StudentSubmission(models.Model):
    application = models.ForeignKey('application.Application', on_delete=models.CASCADE)
    assignment = models.ForeignKey('Assessment', on_delete=models.CASCADE)
    file = models.FileField(upload_to='student_submissions/')
    submitted_at = models.DateTimeField(default=timezone.now)
    attempt_number = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.application.student.user.username} - {self.assignment.title} (Attempt {self.attempt_number})"
