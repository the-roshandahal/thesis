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
        try:
            # Get all applications for the student
            applications = Application.objects.filter(members__user=request.user).select_related('project').prefetch_related('members__user')
            
            # Get assessment data
            from assessment.models import Assessment, StudentSubmission, AssessmentSchema
            from django.utils import timezone
            from django.db.models import Count, Avg, Q
            
            # Get current date
            today = timezone.now().date()
            
            # Get accepted applications
            accepted_applications = applications.filter(status='accepted')
            accepted_projects_count = accepted_applications.count()
            
            # Get student submissions for accepted applications
            submissions = StudentSubmission.objects.filter(
                application__in=accepted_applications
            ).select_related('assignment', 'application')
            
            # Get all assessments that the student has submissions for
            assessments = Assessment.objects.filter(
                id__in=submissions.values_list('assignment_id', flat=True)
            ).distinct()
            
            # Get upcoming assessments (due in next 30 days) - only those the student has access to
            upcoming_assessments = assessments.filter(
                due_date__gte=today,
                due_date__lte=today + timezone.timedelta(days=30)
            ).order_by('due_date')
            
            # Get overdue assessments - only those the student has access to
            overdue_assessments = assessments.filter(due_date__lt=today).exclude(
                id__in=submissions.values_list('assignment_id', flat=True)
            )
            
            # Get recent submissions (last 7 days)
            recent_submissions = submissions.filter(
                submitted_at__gte=today - timezone.timedelta(days=7)
            ).order_by('-submitted_at')
            
            # Calculate statistics
            total_applications = applications.count()
            pending_applications = applications.filter(status='applied').count()
            declined_applications = applications.filter(status='declined').count()
            
            # Get grades data
            graded_submissions = submissions.filter(grades_received__isnull=False)
            average_grade = graded_submissions.aggregate(avg_grade=Avg('grades_received'))['avg_grade'] or 0
            
            # Get notifications
            notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
            unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()
            
            # Get application status distribution for charts
            application_status_data = [
                {'status': 'Applied', 'count': pending_applications, 'color': '#f4ba40'},
                {'status': 'Accepted', 'count': accepted_projects_count, 'color': '#38c786'},
                {'status': 'Declined', 'count': declined_applications, 'color': '#ed5e49'}
            ]
            
            # Get grade distribution for charts
            grade_ranges = [
                {'range': '90-100', 'count': graded_submissions.filter(grades_received__gte=90).count(), 'color': '#38c786'},
                {'range': '80-89', 'count': graded_submissions.filter(grades_received__gte=80, grades_received__lt=90).count(), 'color': '#0c768a'},
                {'range': '70-79', 'count': graded_submissions.filter(grades_received__gte=70, grades_received__lt=80).count(), 'color': '#f4ba40'},
                {'range': '60-69', 'count': graded_submissions.filter(grades_received__gte=60, grades_received__lt=70).count(), 'color': '#ed5e49'},
                {'range': 'Below 60', 'count': graded_submissions.filter(grades_received__lt=60).count(), 'color': '#8590a5'}
            ]
            
            # Convert to JSON for JavaScript
            import json
            application_status_json = json.dumps(application_status_data)
            grade_ranges_json = json.dumps(grade_ranges)
            
        except Exception as e:
            # If there's an error, provide default values
            print(f"Error in student dashboard: {e}")
            applications = Application.objects.filter(members__user=request.user).select_related('project').prefetch_related('members__user')
            accepted_applications = applications.filter(status='accepted')
            accepted_projects_count = accepted_applications.count()
            total_applications = applications.count()
            pending_applications = applications.filter(status='applied').count()
            declined_applications = applications.filter(status='declined').count()
            
            # Default values for other data
            assessments = Assessment.objects.none()
            submissions = StudentSubmission.objects.none()
            upcoming_assessments = Assessment.objects.none()
            overdue_assessments = Assessment.objects.none()
            recent_submissions = StudentSubmission.objects.none()
            notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
            unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()
            average_grade = 0
            
            # Default chart data
            application_status_data = [
                {'status': 'Applied', 'count': pending_applications, 'color': '#f4ba40'},
                {'status': 'Accepted', 'count': accepted_projects_count, 'color': '#38c786'},
                {'status': 'Declined', 'count': declined_applications, 'color': '#ed5e49'}
            ]
            grade_ranges = [
                {'range': '90-100', 'count': 0, 'color': '#38c786'},
                {'range': '80-89', 'count': 0, 'color': '#0c768a'},
                {'range': '70-79', 'count': 0, 'color': '#f4ba40'},
                {'range': '60-69', 'count': 0, 'color': '#ed5e49'},
                {'range': 'Below 60', 'count': 0, 'color': '#8590a5'}
            ]
            
            import json
            application_status_json = json.dumps(application_status_data)
            grade_ranges_json = json.dumps(grade_ranges)
        
        context = {
            'applications': applications,
            'assessments': assessments,
            'submissions': submissions,
            'upcoming_assessments': upcoming_assessments,
            'overdue_assessments': overdue_assessments,
            'recent_submissions': recent_submissions,
            'notifications': notifications,
            'unread_notifications_count': unread_notifications_count,
            
            # Statistics
            'total_applications': total_applications,
            'accepted_projects_count': accepted_projects_count,
            'pending_applications': pending_applications,
            'declined_applications': declined_applications,
            'average_grade': round(average_grade, 1),
            'total_assessments': assessments.count(),
            'completed_assessments': submissions.count(),
            'upcoming_assessments_count': upcoming_assessments.count(),
            'overdue_assessments_count': overdue_assessments.count(),
            
            # Chart data
            'application_status_data': application_status_data,
            'grade_ranges': grade_ranges,
            'application_status_json': application_status_json,
            'grade_ranges_json': grade_ranges_json,
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
        return render(request, 'view_all_notification.html', {'notifications': notifications})
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
