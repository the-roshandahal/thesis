from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from accounts.models import *
from django.contrib.auth.models import User
from projects.models import *
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import *
from application.models import *

from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
def home(request):

    if request.user.is_superuser:
        return render(request, 'admin_dashboard.html')
        return redirect('admin:index')  # Default Django admin dashboard

    elif request.user.is_staff:
        return render(request, 'supervisor_dashboard.html')

    else:
        # Get student's applications
        applications = Application.objects.filter(members__user=request.user).select_related('project').prefetch_related('members__user')
        
        # Get accepted project for assessment data
        accepted_application = applications.filter(status='accepted').first()
        
        # Get assessment data if student has accepted project
        assessments = []
        submissions = []
        total_grade = 0
        completed_assessments = 0
        upcoming_deadlines = []
        
        if accepted_application:
            from assessment.models import Assessment, StudentSubmission
            from datetime import timedelta
            
            # Get assessments for the accepted project
            project = accepted_application.project
            if hasattr(project, 'assessment_schema'):
                schema = project.assessment_schema
                assessments = Assessment.objects.filter(schema=schema).order_by('due_date')
                
                # Get student's submissions
                submissions = StudentSubmission.objects.filter(
                    application=accepted_application,
                    submitted_by=request.user
                ).select_related('assignment')
                
                # Calculate grades and progress
                for submission in submissions:
                    if submission.grades_received is not None:
                        total_grade += submission.grades_received
                        completed_assessments += 1
                
                # Get upcoming deadlines (next 7 days)
                today = timezone.now().date()
                upcoming_deadlines = [
                    assessment for assessment in assessments 
                    if assessment.due_date <= today + timedelta(days=7) and assessment.due_date >= today
                ]
        
        # Get recent notifications
        from .models import Notification
        recent_notifications = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).order_by('-created_at')[:5]
        
        # Get accurate notification counts
        all_notifications = Notification.objects.filter(user=request.user)
        total_notifications = all_notifications.count()
        read_notifications = all_notifications.filter(is_read=True).count()
        unread_notifications = all_notifications.filter(is_read=False).count()
        
        # Calculate overall progress percentage
        overall_progress = 0
        if assessments:
            overall_progress = (completed_assessments / len(assessments)) * 100
        
        # Calculate average grade
        average_grade = 0
        if completed_assessments > 0:
            average_grade = total_grade / completed_assessments
        
        # Get current date for template comparisons
        today = timezone.now().date()
        
        context = {
            'applications': applications,
            'assessments': assessments,
            'submissions': submissions,
            'total_grade': total_grade,
            'completed_assessments': completed_assessments,
            'overall_progress': overall_progress,
            'average_grade': average_grade,
            'upcoming_deadlines': upcoming_deadlines,
            'recent_notifications': recent_notifications,
            'accepted_application': accepted_application,
            'total_notifications': total_notifications,
            'read_notifications': read_notifications,
            'unread_notifications': unread_notifications,
            'today': today,
        }
        return render(request, 'student_dashboard.html', context)



def homepage(request):
    query = request.GET.get('q')
    topic_type = request.GET.get('topic_type')
    availability_filter = request.GET.get('availability', 'all')  # New filter parameter

    # Get all projects initially
    projects = Project.objects.all()
    print(f"DEBUG: Total projects found: {projects.count()}")

    # Apply availability filter if specified
    if availability_filter == 'available':
        # Show only projects that are available for new applications
        # (no accepted applications, only 'applied' or 'declined' applications are fine)
        projects = [p for p in projects if p.is_available_for_application]
        print(f"DEBUG: After 'available' filter: {len(projects)} projects")
    elif availability_filter == 'taken':
        # Show only projects that have accepted applications (are taken)
        projects = [p for p in projects if not p.is_available_for_application]
        print(f"DEBUG: After 'taken' filter: {len(projects)} projects")
    # If 'all' or no filter, show all projects

    if query:
        projects = [p for p in projects if query.lower() in p.title.lower()]

    if topic_type:
        projects = [p for p in projects if p.project_type.lower() == topic_type.lower()]

    # Add availability information to each project
    for project in projects:
        project.is_available = project.is_available_for_application
        print(f"DEBUG: Project '{project.title}' - is_available: {project.is_available}")

    context = {
        'projects': projects,
        'query': query,
        'selected_topic_type': topic_type,
        'selected_availability': availability_filter,
        'total_projects': len(projects),
        'available_count': len([p for p in projects if p.is_available]),
        'taken_count': len([p for p in projects if not p.is_available]),
    }
    
    print(f"DEBUG: Final context - Total: {context['total_projects']}, Available: {context['available_count']}, Taken: {context['taken_count']}")
    
    return render(request, 'index.html', context)

def view_all_notifications(request):
    if request.user.is_authenticated:
        # Fetch all notifications for the logged-in user
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        
        # Calculate accurate notification counts
        total_notifications = notifications.count()
        read_notifications = notifications.filter(is_read=True).count()
        unread_notifications = notifications.filter(is_read=False).count()
        
        context = {
            'notifications': notifications,
            'total_notifications': total_notifications,
            'read_notifications': read_notifications,
            'unread_notifications': unread_notifications,
        }
        return render(request, 'view_all_notification.html', context)
    else:
        # If the user is not authenticated, redirect them to the login page
        return redirect('login')

from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import Notification

@login_required
def mark_notification_as_read_and_redirect(request, notification_id):
    # Fetch the notification for the logged-in user and ensure it's valid
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    
    # Mark it as read
    notification.is_read = True
    print('heter')
    notification.save()

    # Redirect to the URL stored in the notification (or a default URL if not set)
    return redirect(notification.url or reverse('home'))  # Redirect to the URL stored in the notification or fallback to home

@login_required
def mark_all_notifications_as_read(request):
    # Mark all unread notifications as read for the logged-in user
    notifications = Notification.objects.filter(user=request.user, is_read=False)
    notifications.update(is_read=True)

    # Redirect back to the "View All Notifications" page after marking as read
    return HttpResponseRedirect(reverse('view_all_notifications'))

def debug_projects(request):
    """Debug view to check project availability status"""
    from projects.models import Project
    from application.models import Application
    
    projects = Project.objects.all()
    applications = Application.objects.all()
    
    debug_info = []
    
    for project in projects:
        project_info = {
            'id': project.id,
            'title': project.title,
            'availability_field': project.availability,
            'total_applications': project.applications.count(),
            'accepted_applications': project.applications.filter(status='accepted').count(),
            'applied_applications': project.applications.filter(status='applied').count(),
            'declined_applications': project.applications.filter(status='declined').count(),
            'is_available_property': project.is_available_for_application,
        }
        debug_info.append(project_info)
    
    context = {
        'debug_info': debug_info,
        'total_projects': projects.count(),
        'total_applications': applications.count(),
        'accepted_applications': applications.filter(status='accepted').count(),
    }
    
    return render(request, 'debug_projects.html', context)

def fix_project_availability(request):
    """Fix the availability status of all existing projects"""
    from projects.models import Project
    
    projects = Project.objects.all()
    fixed_count = 0
    
    for project in projects:
        old_status = project.availability
        project.update_availability_status()
        if old_status != project.availability:
            fixed_count += 1
    
    messages.success(request, f"Fixed availability status for {fixed_count} projects.")
    return redirect('homepage')
