from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.http import Http404, JsonResponse
from assessment.models import Assessment, StudentSubmission
from projects.models import Project
from .forms import GradeSubmissionForm
from accounts.decorators import supervisor_required
from defaults.models import Notification

@login_required
@supervisor_required
def assessment_list(request):
    """List all assessments that need grading"""
    assessments = Assessment.objects.annotate(
        total_submissions=Count('studentsubmission'),
        graded_submissions=Count('studentsubmission', filter=Q(studentsubmission__grades_received__isnull=False))
    ).order_by('-due_date')

    context = {
        'assessments': assessments,
        'title': 'Assessments for Grading',
        'user_is_supervisor': request.user.is_staff and not request.user.is_superuser,
        'user_is_admin': request.user.is_superuser,
    }
    return render(request, 'grading/assessment_list.html', context)

@login_required
@supervisor_required
def assessment_detail(request, assessment_id):
    """Show all submissions for a specific assessment"""
    assessment = get_object_or_404(Assessment, id=assessment_id)
    submissions = StudentSubmission.objects.filter(
        assignment=assessment
    ).select_related(
        'submitted_by',
        'application__project'
    ).order_by('-submitted_at')

    # Calculate average grade
    avg_grade = submissions.aggregate(Avg('grades_received'))['grades_received__avg']
    
    # Calculate grading progress
    total_submissions = submissions.count()
    graded_submissions = submissions.filter(grades_received__isnull=False).count()
    grading_progress = (graded_submissions / total_submissions * 100) if total_submissions > 0 else 0

    published_status = 'unpublished'
    for sub in submissions:
        if sub.published_status == 'published':
            published_status = 'published'


    context = {
        'assessment': assessment,
        'submissions': submissions,
        'avg_grade': avg_grade,
        'total_submissions': total_submissions,
        'graded_submissions': graded_submissions,
        'published_status': published_status,
        'grading_progress': grading_progress,
        'title': f'Submissions for {assessment.title}',
        'user_is_supervisor': request.user.is_staff and not request.user.is_superuser,
        'user_is_admin': request.user.is_superuser,
    }
    return render(request, 'grading/assessment_detail.html', context)

@login_required
@supervisor_required
def grade_submission(request, submission_id):
    submission = get_object_or_404(
        StudentSubmission.objects.select_related('assignment'),
        id=submission_id
    )
    
    # Ensure assessment exists
    if not submission.assignment:
        raise Http404("This submission has no associated assessment")

    if request.method == 'POST':
        form = GradeSubmissionForm(request.POST, instance=submission)
        if form.is_valid():
            # Check if this is a new grade assignment or grade update
            old_grade = submission.grades_received
            old_feedback = submission.feedback
            
            form.save()
            
            # Send notification to student about grade assignment
            try:
                if old_grade is None and submission.grades_received is not None:
                    # New grade assigned
                    notification_message = f"Your submission for '{submission.assignment.title}' has been graded. Grade: {submission.grades_received}/{submission.assignment.weight}"
                elif old_grade != submission.grades_received:
                    # Grade updated
                    notification_message = f"Your grade for '{submission.assignment.title}' has been updated. New grade: {submission.grades_received}/{submission.assignment.weight}"
                elif old_feedback != submission.feedback:
                    # Feedback updated
                    notification_message = f"Your feedback for '{submission.assignment.title}' has been updated."
                else:
                    # No significant changes
                    notification_message = None
                
                if notification_message:
                    Notification.objects.create(
                        user=submission.submitted_by,
                        message=notification_message,
                        url="/home/"  # Link to student dashboard where grades are displayed
                    )
                    print(f"DEBUG: Created notification for student {submission.submitted_by.email}: {notification_message}")
            except Exception as e:
                print(f"DEBUG: Error creating notification for student {submission.submitted_by.email}: {str(e)}")
            
            messages.success(request, 'Grade submitted successfully!')
            return redirect('grading:assessment_detail', assessment_id=submission.assignment.id)
    else:
        form = GradeSubmissionForm(instance=submission)

    context = {
        'submission': submission,
        'form': form,
        'assessment': submission.assignment,  # Make sure this is included
        'title': f'Grading {submission.assignment.title}',
        'user_is_supervisor': request.user.is_staff and not request.user.is_superuser,
        'user_is_admin': request.user.is_superuser,
    }
    return render(request, 'grading/grade_submission.html', context)

#AJAX view for loading submission files in modal
@login_required
@supervisor_required
def submission_files(request, submission_id):
    """AJAX view for loading submission files in modal"""
    submission = get_object_or_404(StudentSubmission, id=submission_id)
    files = submission.files.all()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'grading/files_partial.html', {'files': files})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
@supervisor_required
def publish_grades(request, assessment_id):
    """Publish grades for all submissions in an assessment"""
    print(f"DEBUG: publish_grades called for assessment_id: {assessment_id}")
    print(f"DEBUG: Request method: {request.method}")
    print(f"DEBUG: Current user: {request.user.email}")
    
    if request.method != 'POST':
        print(f"DEBUG: Invalid method {request.method}, returning 405")
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)
    
    assessment = get_object_or_404(Assessment, id=assessment_id)
    print(f"DEBUG: Found assessment: {assessment.title}")
    
    # Check if user is the supervisor of any project in this assessment
    # This ensures only relevant supervisors can publish grades
    submissions = StudentSubmission.objects.filter(assignment=assessment)
    print(f"DEBUG: Found {submissions.count()} submissions for assessment")
    
    if not submissions.exists():
        print(f"DEBUG: No submissions found")
        return JsonResponse({'error': 'No submissions found for this assessment'}, status=404)
    
    # Update all submissions to published status
    print(f"DEBUG: Updating submissions to published status")
    updated_count = submissions.update(published_status='published')
    print(f"DEBUG: Updated {updated_count} submissions")
    
    if updated_count > 0:
        # Create notifications for all students whose grades were published
        notifications_created = 0
        for submission in submissions:
            try:
                # Create notification for the student
                notification = Notification.objects.create(
                    user=submission.submitted_by,
                    message=f"Your grades for '{assessment.title}' have been published and are now available for viewing.",
                    url="/home/"  # Link to student dashboard where grades are displayed
                )
                notifications_created += 1
                print(f"DEBUG: Created notification for student {submission.submitted_by.email}")
            except Exception as e:
                print(f"DEBUG: Error creating notification for student {submission.submitted_by.email}: {str(e)}")
                continue
        
        print(f"DEBUG: Created {notifications_created} notifications")
        
        messages.success(request, f'Grades published successfully for {updated_count} submission(s)! Students have been notified.')
        print(f"DEBUG: Success - published {updated_count} submissions and created {notifications_created} notifications")
        return JsonResponse({
            'success': True, 
            'message': f'Grades published for {updated_count} submission(s)! Students have been notified.',
            'notifications_created': notifications_created
        })
    else:
        print(f"DEBUG: No submissions were updated")
        return JsonResponse({'error': 'No submissions were updated'}, status=400)