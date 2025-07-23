from django.shortcuts import render, redirect
from assessment.models import *
from django.contrib import messages
from django.utils.dateparse import parse_date
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from .models import AssessmentSchema
from django.utils.text import get_valid_filename


def assessment_schema(request):
    schema = AssessmentSchema.objects.first()  # Only one allowed
    return render(request, 'assessment/assessment_schema.html', {
        'schema': schema
    })


def create_assessment_schema(request):
    if AssessmentSchema.objects.exists():
        return redirect('assessment_schema')

    if request.method == "POST":
        try:
            # Basic schema info
            schema_name = request.POST.get('schema_name')
            start_date = parse_date(request.POST.get('schema_start_date'))
            end_date = parse_date(request.POST.get('schema_end_date'))

            if not schema_name or not start_date or not end_date:
                messages.error(request, "Please fill in all schema fields correctly.")
                return render(request, 'assessment/create_schema.html')

            # Create schema object
            schema = AssessmentSchema.objects.create(
                name=schema_name,
                start_date=start_date,
                end_date=end_date,
            )

            # Identify assignment indices dynamically
            assignment_indices = set()
            for key in request.POST.keys():
                if key.startswith('assignment_name_'):
                    idx = key.split('_')[-1]
                    assignment_indices.add(idx)
            assignment_indices = sorted(assignment_indices, key=int)

            # Process each assignment
            for idx in assignment_indices:
                name = request.POST.get(f'assignment_name_{idx}')
                due_date = parse_date(request.POST.get(f'assignment_due_{idx}'))
                submission_type = request.POST.get(f'submission_type_{idx}')
                weight_raw = request.POST.get(f'assignment_weight_{idx}')
                details = request.POST.get(f'assignment_detail_{idx}', '')

                # Validate required fields
                if not name or not due_date or not weight_raw:
                    messages.error(request, f"Missing required fields for assignment #{idx}")
                    schema.delete()  # rollback schema creation
                    return render(request, 'assessment/create_schema.html')

                try:
                    weight = float(weight_raw)
                except ValueError:
                    messages.error(request, f"Invalid weight for assignment #{idx}")
                    schema.delete()
                    return render(request, 'assessment/create_schema.html')

                # Create Assignment object
                assignment = Assessment.objects.create(
                    schema=schema,
                    title=name,
                    due_date=due_date,
                    weight=weight,
                    description=details,
                    submission_type=submission_type
                )

                # Helper function to process uploaded files
                def process_uploaded_files(file_key, base_path, model_class):
                    if file_key in request.FILES:
                        for i, file in enumerate(request.FILES.getlist(file_key)):
                            # Get custom name from form or use original name
                            custom_base = request.POST.get(f'{file_key}_name_{i}', '')
                            if not custom_base:  # If no custom name provided
                                custom_base = os.path.splitext(file.name)[0]
                            
                            # Preserve original extension
                            original_ext = os.path.splitext(file.name)[1]
                            custom_name = f"{custom_base}{original_ext}"
                            
                            # Sanitize filename
                            custom_name = get_valid_filename(custom_name)
                            
                            # Create file path
                            file_path = f"{base_path}/schema_{schema.id}/assessment_{assignment.id}/{custom_name}"
                            
                            # Handle duplicate filenames
                            base, ext = os.path.splitext(custom_name)
                            counter = 1
                            while default_storage.exists(file_path):
                                custom_name = f"{base}_{counter}{ext}"
                                file_path = f"{base_path}/schema_{schema.id}/assessment_{assignment.id}/{custom_name}"
                                counter += 1

                            # Save file
                            default_storage.save(file_path, file)
                            
                            # Create database record
                            model_class.objects.create(
                                assessment=assignment,
                                name=custom_name,
                                file=file_path
                            )

                # Process assignment detail files
                process_uploaded_files(
                    file_key=f'assignment_files_{idx}',
                    base_path='assessment_details/details',
                    model_class=AssessmentDetailFile
                )

                # Process sample files
                process_uploaded_files(
                    file_key=f'sample_files_{idx}',
                    base_path='assessment_samples/samples',
                    model_class=AssessmentSampleFile
                )

            messages.success(request, "Assessment schema created successfully!")
            return redirect('assessment_schema')

        except Exception as e:
            messages.error(request, f"Error creating schema: {str(e)}")
            if 'schema' in locals():
                schema.delete()
            return render(request, 'assessment/create_schema.html')

    return render(request, 'assessment/create_schema.html')


def edit_schema(request,id):
    pass



def add_assessment(request,id):
    pass


def edit_assessment(request,id):
    pass


from django.utils import timezone
from datetime import date

def student_view_assignment(request):
    schema = AssessmentSchema.objects.first()  # or your logic to get the schema
    
    if schema and hasattr(schema, 'assessments'):
        today = date.today()  # Using date.today() instead of timezone.now().date() for simplicity
        assessments_with_days = []
        
        for assessment in schema.assessments.all():
            assessment_data = {
                'obj': assessment,
                'due_date': assessment.due_date,
                'title': assessment.title,
                'description': assessment.description,
                'weight': assessment.weight,
                'submission_type' : assessment.submission_type,
                'detail_files': assessment.detail_files.all(),
                'sample_files': assessment.sample_files.all(),
            }
            
            if assessment.due_date:
                delta = assessment.due_date - today
                assessment_data['days_remaining'] = delta.days
                assessment_data['days_absolute'] = abs(delta.days)
                assessment_data['is_overdue'] = delta.days < 0
            else:
                assessment_data['days_remaining'] = None
                assessment_data['days_absolute'] = None
                assessment_data['is_overdue'] = False
                
            assessments_with_days.append(assessment_data)
        
        context = {
            'schema': schema,
            'assessments_with_days': assessments_with_days,
        }
    else:
        context = {
            'schema': schema,
            'assessments_with_days': [],
        }

    return render(request, 'assessment/student_view_assignment.html', context)
