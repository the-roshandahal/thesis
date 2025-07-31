from django import forms
from assessment.models import StudentSubmission
from django.core.exceptions import ValidationError

class GradeSubmissionForm(forms.ModelForm):
    class Meta:
        model = StudentSubmission
        fields = ['grades_received', 'feedback']
    
    def clean_grades_received(self):
        grade = self.cleaned_data['grades_received']
        total_marks = self.instance.assignment.weight
        
        if grade > total_marks:
            raise ValidationError(
                f'Grade cannot exceed total marks ({total_marks})'
            )
        return grade