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
            from django.utils import timezone
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

    projects = Project.objects.all()

    if query:
        projects = projects.filter(title__icontains=query)  # or any field you want to search in

    if topic_type:
        projects = projects.filter(project_type__iexact=topic_type)

    context = {
        'projects': projects,
        'query': query,
        'selected_topic_type': topic_type,
    }
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
