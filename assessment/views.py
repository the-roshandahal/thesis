from django.shortcuts import render, redirect
from assessment.models import *
from django.contrib import messages
from django.utils.dateparse import parse_date


from django.shortcuts import render, redirect
from .models import AssessmentSchema

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
                    description=details
                )


                # Save Assignment Files with custom names
                # Save Assignment Detail Files with custom names
                files_key = f'assignment_files_{idx}'
                if files_key in request.FILES:
                    for i, file in enumerate(request.FILES.getlist(files_key)):
                        custom_name = request.POST.get(f'assignment_file_name_{idx}_{i}', file.name)
                        AssessmentDetailFile.objects.create(
                            assessment=assignment,
                            file=file,
                            name=custom_name
                        )

                # Save Sample Files with custom names
                sample_key = f'sample_files_{idx}'
                if sample_key in request.FILES:
                    for i, file in enumerate(request.FILES.getlist(sample_key)):
                        custom_name = request.POST.get(f'sample_file_name_{idx}_{i}', file.name)
                        AssessmentSampleFile.objects.create(
                            assessment=assignment,
                            file=file,
                            name=custom_name
                        )


            messages.success(request, "Assessment Schema and assignments created successfully.")
            return redirect('assessment_schema')  # Change to your actual success URL

        except Exception as e:
            messages.error(request, f"Error creating assessment schema: {e}")
            print(e)

    # For GET request or if errors, render form template
    return render(request, 'assessment/create_schema.html')




def edit_schema(request,id):
    pass



def add_assessment(request,id):
    pass


def edit_assessment(request,id):
    pass