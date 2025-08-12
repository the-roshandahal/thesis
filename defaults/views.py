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
        applications = Application.objects.filter(members__user=request.user).select_related('project').prefetch_related('members__user')
        context = {
            'applications': applications,
        }
        return render(request, 'student_dashboard.html',context)



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
