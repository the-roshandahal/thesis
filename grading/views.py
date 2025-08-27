from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.http import Http404, JsonResponse
from assessment.models import Assessment, StudentSubmission
from projects.models import Project
from .forms import GradeSubmissionForm
from django.urls import reverse
from defaults.models import Notification  
from application.models import *

@login_required
def assessment_list(request):
    assessments = []

    for assessment in Assessment.objects.all().prefetch_related('detail_files', 'sample_files'):
        # Total expected submissions
        if assessment.submission_type == "individual":
            expected_total = ApplicationMember.objects.filter(
                application__status="accepted"
            ).count()
        else:  # group
            expected_total = Application.objects.filter(
                status="accepted",
                application_type="group"
            ).count()

        # Total submitted
        submitted_total = StudentSubmission.objects.filter(assignment=assessment).count()

        # Total graded
        graded_total = StudentSubmission.objects.filter(
            assignment=assessment,
            grades_received__isnull=False
        ).count()

        # Left to grade
        left_to_grade = submitted_total - graded_total

        assessments.append({
            'assessment': assessment,
            'title': assessment.title,
            'due_date': assessment.due_date,
            'weight': assessment.weight,
            'submission_type': assessment.submission_type,
            'total_submissions': submitted_total,
            'graded_submissions': graded_total,
            'expected_total': expected_total,
            'left_to_grade': left_to_grade,
        })

    context = {
        'assessments': assessments,
        'title': 'Assessments for Grading'
    }
    return render(request, 'grading/assessment_list.html', context)
from django.db.models import Avg
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from datetime import date

@login_required
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

    # Total submissions
    total_submissions = submissions.count()

    # Total graded submissions
    graded_submissions = submissions.filter(grades_received__isnull=False).count()

    # Left to grade
    left_to_grade = total_submissions - graded_submissions

    # Total expected submissions
    if assessment.submission_type == "individual":
        expected_total = ApplicationMember.objects.filter(
            application__status="accepted"
        ).count()
    else:  # group
        expected_total = Application.objects.filter(
            status="accepted",
            application_type="group"
        ).count()

    # Grading progress %
    grading_progress = (graded_submissions / total_submissions * 100) if total_submissions > 0 else 0

    # Published status
    published_status = 'unpublished'
    for sub in submissions:
        if sub.published_status == 'published':
            published_status = 'published'
    today = date.today()
    can_publish = False
    if assessment.submit_by and assessment.submit_by <= today:
        can_publish = True    
    if expected_total == total_submissions:
        can_publish = True

    context = {
        'assessment': assessment,
        'can_publish': can_publish,
        'submissions': submissions,
        'avg_grade': avg_grade,
        'total_submissions': total_submissions,
        'graded_submissions': graded_submissions,
        'left_to_grade': left_to_grade,
        'expected_total': expected_total,
        'published_status': published_status,
        'grading_progress': grading_progress,
        'title': f'Submissions for {assessment.title}'
    }

    return render(request, 'grading/assessment_detail.html', context)


@login_required
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
            form.save()
            Notification.objects.create(
                user=submission.submitted_by,  
                message=f"Your submission for '{submission.assignment.title}' has been graded.",
                url=reverse('grading:assessment_detail', args=[submission.assignment.id])
            )

            messages.success(request, 'Grade submitted successfully!')
            return redirect('grading:assessment_detail', assessment_id=submission.assignment.id)
        
    else:
        form = GradeSubmissionForm(instance=submission)

    context = {
        'submission': submission,
        'form': form,
        'assessment': submission.assignment,  # Make sure this is included
        'title': f'Grading {submission.assignment.title}'
    }
    return render(request, 'grading/grade_submission.html', context)

#AJAX view for loading submission files in modal
@login_required
def submission_files(request, submission_id):
    """AJAX view for loading submission files in modal"""
    submission = get_object_or_404(StudentSubmission, id=submission_id)
    files = submission.files.all()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'grading/files_partial.html', {'files': files})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)




from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

@login_required
def publish_grades(request, assessment_id):
    """
    Publish grades for an assessment with confirmation modal.
    """
    assessment = get_object_or_404(Assessment, id=assessment_id)
    submissions = StudentSubmission.objects.filter(assignment=assessment)

    # Total expected submissions
    if assessment.submission_type == "individual":
        expected_total = ApplicationMember.objects.filter(
            application__status="accepted"
        ).count()
    else:
        expected_total = Application.objects.filter(
            status="accepted",
            application_type="group"
        ).count()

    submitted_total = submissions.count()
    graded_total = submissions.filter(grades_received__isnull=False).count()

    pending_submissions = expected_total - submitted_total
    ungraded_submissions = submitted_total - graded_total

    if request.method == "POST":
        # Publish graded submissions
        submissions.filter(grades_received__isnull=False).update(published_status='published')
        messages.success(request, "Grades published successfully for all graded submissions.")
        return redirect('grading:assessment_detail', assessment_id=assessment.id)

    context = {
        'assessment': assessment,
        'pending_submissions': pending_submissions,
        'ungraded_submissions': ungraded_submissions,
    }
    return render(request, 'grading/publish_grades_confirm.html', context)
