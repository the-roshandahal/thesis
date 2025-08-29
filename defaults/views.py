from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from application.models import Application
from projects.models import Project
from assessment.models import Assessment, StudentSubmission, AssessmentSchema
from .models import Notification
from django.utils import timezone
from django.db.models import Count, Avg, Q
import json
from .decorators import *

def homepage(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            # Superuser sees admin dashboard
            from .dashboard_views import admin_dashboard
            return admin_dashboard(request)
        elif request.user.is_staff:
            # Staff (supervisors) see supervisor dashboard
            from .dashboard_views import supervisor_dashboard
            return supervisor_dashboard(request)
        else:
            # Regular users (students) see student dashboard
            from .dashboard_views import student_dashboard
            return student_dashboard(request)
    
    """Public homepage view with project search functionality."""
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


@login_required
def home(request):
    """Home view that redirects to appropriate dashboard based on user role."""
    if request.user.is_superuser:
        # Superuser sees admin dashboard
        from .dashboard_views import admin_dashboard
        return admin_dashboard(request)
    elif request.user.is_staff:
        # Staff (supervisors) see supervisor dashboard
        from .dashboard_views import supervisor_dashboard
        return supervisor_dashboard(request)
    else:
        # Regular users (students) see student dashboard
        from .dashboard_views import student_dashboard
        return student_dashboard(request)

@login_required
def view_all_notifications(request):
    """View all notifications for the logged-in user."""
    if request.user.is_authenticated:
        # Fetch all notifications for the logged-in user
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        return render(request, 'view_all_notification.html', {'notifications': notifications})
    else:
        # If the user is not authenticated, redirect them to the login page
        return redirect('login')


@login_required
def mark_notification_as_read_and_redirect(request, notification_id):
    """Mark a notification as read and redirect to its URL."""
    # Fetch the notification for the logged-in user and ensure it's valid
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    
    # Mark it as read
    notification.is_read = True
    notification.save()

    # Redirect to the URL stored in the notification (or a default URL if not set)
    return redirect(notification.url or reverse('home'))


@login_required
def mark_all_notifications_as_read(request):
    """Mark all unread notifications as read for the logged-in user."""
    # Mark all unread notifications as read for the logged-in user
    notifications = Notification.objects.filter(user=request.user, is_read=False)
    notifications.update(is_read=True)

    # Redirect back to the "View All Notifications" page after marking as read
    return HttpResponseRedirect(reverse('view_all_notifications'))
