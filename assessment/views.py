from django.shortcuts import render, redirect
from assessment.models import *
from django.contrib import messages
from django.utils.dateparse import parse_date
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from .models import AssessmentSchema
from django.utils.text import get_valid_filename
from django.utils import timezone
from datetime import date
from application.models import *

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
                submit_by = parse_date(request.POST.get(f'assignment_due_{idx}'))
                submission_type = request.POST.get(f'submission_type_{idx}')
                weight_raw = request.POST.get(f'assignment_weight_{idx}')
                details = request.POST.get(f'assignment_detail_{idx}', '')

                # Validate required fields
                if not name or not due_date or not weight_raw:
                    messages.error(request, f"Missing required fields for assignment #{idx}")
                    schema.delete()  # rollback schema creation
                    return render(request, 'assessment/create_schema.html')
                
                # Validate required fields
                if not name or not submit_by or not weight_raw:
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
                    submit_by=submit_by,
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


from datetime import date
from django.shortcuts import render
from .models import AssessmentSchema, StudentSubmission, Assessment
from application.models import ApplicationMember

def student_view_assignment(request):
    has_accepted_project = ApplicationMember.objects.filter(
        user=request.user,
        application__status='accepted'
    ).exists()

    schema = AssessmentSchema.objects.first()

    context = {
        'has_accepted_project': has_accepted_project,
        'schema': schema if has_accepted_project else None,
        'assessments_with_days': [],
    }

    if has_accepted_project and schema and hasattr(schema, 'assessments'):
        today = date.today()
        member = ApplicationMember.objects.filter(
            user=request.user,
            application__status='accepted'
        ).select_related('application').first()

        is_leader = member.is_leader if member else False
        application = member.application if member else None

        # Get all submissions by this user
        user_submissions = StudentSubmission.objects.filter(
            submitted_by=request.user
        ).select_related('assignment')

        # If group: get leader submission
        group_leader = ApplicationMember.objects.filter(
            application=application,
            is_leader=True
        ).first() if application else None

        leader_submissions = StudentSubmission.objects.filter(
            submitted_by=group_leader.user
        ).select_related('assignment') if group_leader else []

        assessments_with_days = []

        for assessment in schema.assessments.all().prefetch_related('detail_files', 'sample_files'):
            delta = assessment.due_date - today if assessment.due_date else None
            submit_by_passed = assessment.submit_by < today if assessment.submit_by else False

            # Did the current user submit?
            has_submission = any(sub.assignment_id == assessment.id for sub in user_submissions)

            # Did the group leader submit (relevant only if group and not leader)?
            group_leader_submitted = (
                assessment.submission_type == 'group' and
                not is_leader and
                any(sub.assignment_id == assessment.id for sub in leader_submissions)
            )

            leader_submission = next(
                (sub for sub in leader_submissions if sub.assignment_id == assessment.id),
                None
            ) if group_leader_submitted else None

            assessments_with_days.append({
                'obj': assessment,
                'due_date': assessment.due_date,
                'title': assessment.title,
                'submit_by': assessment.submit_by,
                'description': assessment.description,
                'weight': assessment.weight,
                'submission_type': assessment.submission_type,
                'detail_files': assessment.detail_files.all(),
                'sample_files': assessment.sample_files.all(),
                'days_remaining': delta.days if delta else None,
                'days_absolute': abs(delta.days) if delta else None,
                'is_overdue': delta.days < 0 if delta else False,
                'is_submit_by_passed': submit_by_passed,
                'can_attempt': (
                    assessment.submission_type != 'group' or
                    (assessment.submission_type == 'group' and is_leader)
                ),
                'has_submission': has_submission,
                'group_leader_submitted': group_leader_submitted,
                'leader_submission': leader_submission,
            })

        context['assessments_with_days'] = assessments_with_days

    return render(request, 'assessment/student_view_assignment.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import Assessment, StudentSubmission, SubmissionFile
from application.models import Application  # Ensure this is correct
from django.contrib.auth.decorators import login_required

@login_required
def attempt_assessment(request, id):
    assignment = get_object_or_404(Assessment, id=id)
    application = get_object_or_404(
        Application.objects.filter(members__user=request.user, status='accepted')
    )

    if request.method == 'POST':
        files = request.FILES.getlist('files')
        if not files:
            messages.error(request, "Please upload at least one file.")
            return redirect(request.path)

        # Count previous attempts
        previous_attempts = StudentSubmission.objects.filter(
            assignment=assignment, application=application).count()

        # Create new submission
        submission = StudentSubmission.objects.create(
            application=application,
            assignment=assignment,
            submitted_by=request.user,
            attempt_number=previous_attempts + 1
        )

        for f in files:
            SubmissionFile.objects.create(submission=submission, file=f)

        messages.success(request, "Assignment submitted successfully.")
        return redirect('student_view_assignment')  # update with your actual view name

    return render(request, 'assessment/attempt_assessment.html', {
        'assignment': assignment
    })


import os
from django.shortcuts import get_object_or_404, render, redirect
from .models import * # adjust if needed

def view_submission(request, assessment_id):
    assessment = get_object_or_404(Assessment, id=assessment_id)
    member = ApplicationMember.objects.filter(
        user=request.user,
        application__status='accepted'
    ).select_related('application').first()
    is_leader = member.is_leader if member else False
    application = member.application if member else None

    # Determine whose submissions to fetch
    if assessment.submission_type == 'group' and not is_leader:
        leader = ApplicationMember.objects.filter(application=application, is_leader=True).first()
        submitted_user = leader.user if leader else request.user
    else:
        submitted_user = request.user

    all_attempts = StudentSubmission.objects.filter(
        assignment=assessment,
        submitted_by=submitted_user
    ).order_by('-submitted_at')

    attempt_id = request.GET.get('attempt')
    current_submission = (get_object_or_404(all_attempts, id=attempt_id)
                          if attempt_id else all_attempts.first())
    if not current_submission:
        return redirect('attempt_assessment', assessment_id=assessment_id)

    for file in current_submission.files.all():
        file.basename = os.path.basename(file.file.name)

    # Deadline check
    today = date.today()
    is_submit_by_passed = assessment.submit_by < today if assessment.submit_by else False

    # Group submission check
    other_submission_exists = False
    if assessment.submission_type == 'group' and not is_leader:
        other_submission_exists = all_attempts.exists()

    can_submit_new_attempt = not (is_submit_by_passed or other_submission_exists)

    context = {
        'assessment': assessment,
        'submission': current_submission,
        'all_attempts': all_attempts,
        'can_submit_new_attempt': can_submit_new_attempt,
        'detail_files': assessment.detail_files.all(),
        'sample_files': assessment.sample_files.all(),
    }
    return render(request, 'assessment/view_submission.html', context)
