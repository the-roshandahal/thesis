from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg
from django.http import JsonResponse
from assessment.models import StudentSubmission
from projects.models import Project
from .forms import GradeSubmissionForm

@login_required
def grading_dashboard(request):
    """Main grading dashboard showing all projects"""
    projects = Project.objects.annotate(
        total_applications=Count('applications'),
        total_submissions=Count('applications__studentsubmission')
    ).order_by('-created')

    context = {
        'projects': projects,
        'title': 'Grading Dashboard'
    }
    return render(request, 'grading/grading.html', context)

@login_required
def view_project_submissions(request, project_id):
    """View all submissions for a specific project"""
    project = get_object_or_404(Project, id=project_id)
    submissions = StudentSubmission.objects.filter(
        application__project=project
    ).select_related(
        'assignment', 
        'submitted_by',
        'application'
    ).prefetch_related('files').order_by('-submitted_at')

    # Calculate average grade
    avg_grade = submissions.aggregate(Avg('grades_received'))['grades_received__avg']

    context = {
        'project': project,
        'submissions': submissions,
        'avg_grade': avg_grade,
        'title': f'Submissions for {project.title}'
    }
    return render(request, 'grading/project_submissions.html', context)

@login_required
def grade_submission(request, submission_id):
    """Grade an individual submission"""
    submission = get_object_or_404(
        StudentSubmission.objects.select_related(
            'application__project',
            'assignment',
            'submitted_by'
        ), 
        id=submission_id
    )

    if request.method == 'POST':
        form = GradeSubmissionForm(request.POST, instance=submission)
        if form.is_valid():
            form.save()
            messages.success(request, 'Grade submitted successfully!')
            
            # Redirect back to project submissions
            return redirect('project_submissions', 
                          project_id=submission.application.project.id)
    else:
        form = GradeSubmissionForm(instance=submission)
    print(submission.assignment.weight)
    context = {
        'submission': submission,
        'form': form,
        'title': f'Grading {submission.assignment.title}'
    }
    return render(request, 'grading/grade_submission.html', context)

@login_required
def submission_files(request, submission_id):
    """AJAX view for loading submission files in modal"""
    submission = get_object_or_404(StudentSubmission, id=submission_id)
    files = submission.files.all()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'grading/files_partial.html', {'files': files})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)