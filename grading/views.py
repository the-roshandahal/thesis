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

@login_required
def assessment_list(request):
    """List all assessments that need grading"""
    assessments = Assessment.objects.annotate(
        total_submissions=Count('studentsubmission'),
        graded_submissions=Count('studentsubmission', filter=Q(studentsubmission__grades_received__isnull=False))
    ).order_by('-due_date')

    context = {
        'assessments': assessments,
        'title': 'Assessments for Grading'
    }
    return render(request, 'grading/assessment_list.html', context)

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