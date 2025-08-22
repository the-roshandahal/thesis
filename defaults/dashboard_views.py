from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Avg, Q
from application.models import Application
from projects.models import Project
from assessment.models import Assessment, StudentSubmission, AssessmentSchema
from .models import Notification
import json


@login_required
def student_dashboard(request):
    """Student dashboard view with statistics, charts, and project information."""
    try:
        # Get current date
        today = timezone.now().date()
        
        # Get applications for this student
        applications = Application.objects.filter(members__user=request.user).select_related('project')
        total_applications = applications.count()
        accepted_projects_count = applications.filter(status='accepted').count()
        pending_applications = applications.filter(status='applied').count()
        declined_applications = applications.filter(status='declined').count()
        
        # Get accepted applications to find submissions
        accepted_applications = applications.filter(status='accepted')
        
        # Get submissions for accepted applications
        submissions = StudentSubmission.objects.filter(
            application__in=accepted_applications
        ).select_related('assignment', 'application', 'submitted_by')
        
        # Get assessments that have submissions
        assessments = Assessment.objects.filter(
            id__in=submissions.values_list('assignment_id', flat=True)
        ).distinct()
        
        # Get upcoming assessments (due in next 30 days)
        upcoming_assessments = assessments.filter(
            due_date__gte=today,
            due_date__lte=today + timezone.timedelta(days=30)
        ).order_by('due_date')
        
        # Get overdue assessments
        overdue_assessments = assessments.filter(due_date__lt=today).exclude(
            id__in=submissions.values_list('assignment_id', flat=True)
        )
        
        # Get recent submissions (last 7 days)
        recent_submissions = submissions.filter(
            submitted_at__gte=today - timezone.timedelta(days=7)
        ).order_by('-submitted_at')
        
        # Get grades data
        graded_submissions = submissions.filter(grades_received__isnull=False)
        average_grade = graded_submissions.aggregate(avg_grade=Avg('grades_received'))['avg_grade'] or 0
        
        # Get notifications
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
        unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()
        
        # Prepare chart data
        application_status_data = [
            {'status': 'Applied', 'count': pending_applications, 'color': '#f4ba40'},
            {'status': 'Accepted', 'count': accepted_projects_count, 'color': '#38c786'},
            {'status': 'Declined', 'count': declined_applications, 'color': '#ed5e49'}
        ]
        
        # Grade distribution for charts
        grade_ranges = [
            {'range': '90-100', 'count': graded_submissions.filter(grades_received__gte=90).count(), 'color': '#38c786'},
            {'range': '80-89', 'count': graded_submissions.filter(grades_received__gte=80, grades_received__lt=90).count(), 'color': '#0c768a'},
            {'range': '70-79', 'count': graded_submissions.filter(grades_received__gte=70, grades_received__lt=80).count(), 'color': '#f4ba40'},
            {'range': '60-69', 'count': graded_submissions.filter(grades_received__gte=60, grades_received__lt=70).count(), 'color': '#ed5e49'},
            {'range': 'Below 60', 'count': graded_submissions.filter(grades_received__lt=60).count(), 'color': '#8590a5'}
        ]
        
        # Convert to JSON for JavaScript
        application_status_json = json.dumps(application_status_data)
        grade_ranges_json = json.dumps(grade_ranges)
        
    except Exception as e:
        # If there's an error, provide default values
        print(f"Error in student dashboard: {e}")
        applications = Application.objects.filter(members__user=request.user)
        total_applications = applications.count()
        accepted_projects_count = applications.filter(status='accepted').count()
        pending_applications = applications.filter(status='applied').count()
        declined_applications = applications.filter(status='declined').count()
        
        # Default values for other data
        accepted_applications = applications.filter(status='accepted')
        submissions = StudentSubmission.objects.none()
        assessments = Assessment.objects.none()
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
        
        application_status_json = json.dumps(application_status_data)
        grade_ranges_json = json.dumps(grade_ranges)
    
    context = {
        'applications': applications,
        'total_applications': total_applications,
        'accepted_projects_count': accepted_projects_count,
        'pending_applications': pending_applications,
        'declined_applications': declined_applications,
        
        'assessments': assessments,
        'submissions': submissions,
        'upcoming_assessments': upcoming_assessments,
        'overdue_assessments': overdue_assessments,
        'recent_submissions': recent_submissions,
        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count,
        'average_grade': round(average_grade, 1),
        
        # Chart data
        'application_status_data': application_status_data,
        'grade_ranges': grade_ranges,
        'application_status_json': application_status_json,
        'grade_ranges_json': grade_ranges_json,
    }
    
    return render(request, 'student_dashboard.html', context)


@login_required
def supervisor_dashboard(request):
    """Supervisor dashboard view with project statistics, charts, and student information."""
    try:
        # Get current date
        today = timezone.now().date()
        
        # Get projects created by this supervisor
        supervisor_projects = Project.objects.filter(supervisor=request.user)
        total_projects = supervisor_projects.count()
        available_projects = supervisor_projects.filter(availability='available').count()
        ongoing_projects = supervisor_projects.filter(availability='ongoing').count()
        completed_projects = supervisor_projects.filter(availability='completed').count()
        
        # Get applications for supervisor's projects
        project_applications = Application.objects.filter(
            project__supervisor=request.user
        ).select_related('project').prefetch_related('members__user')
        
        total_applications = project_applications.count()
        pending_applications = project_applications.filter(status='applied').count()
        accepted_applications = project_applications.filter(status='accepted').count()
        declined_applications = project_applications.filter(status='declined').count()
        
        # Get accepted applications to find active students
        accepted_applications_list = project_applications.filter(status='accepted')
        active_students = accepted_applications_list.values('members__user').distinct().count()
        
        # Get assessments and submissions for supervisor's projects
        all_assessments = Assessment.objects.all()
        
        # Get submissions for accepted applications
        submissions = StudentSubmission.objects.filter(
            application__in=accepted_applications_list
        ).select_related('assignment', 'application', 'submitted_by')
        
        # Get assessments that have submissions
        assessments_with_submissions = all_assessments.filter(
            id__in=submissions.values_list('assignment_id', flat=True)
        ).distinct()
        
        # Get upcoming assessments (due in next 30 days)
        upcoming_assessments = assessments_with_submissions.filter(
            due_date__gte=today,
            due_date__lte=today + timezone.timedelta(days=30)
        ).order_by('due_date')
        
        # Get overdue assessments
        overdue_assessments = assessments_with_submissions.filter(due_date__lt=today).exclude(
            id__in=submissions.values_list('assignment_id', flat=True)
        )
        
        # Get recent submissions (last 7 days)
        recent_submissions = submissions.filter(
            submitted_at__gte=today - timezone.timedelta(days=7)
        ).order_by('-submitted_at')
        
        # Get grades data
        graded_submissions = submissions.filter(grades_received__isnull=False)
        average_grade = graded_submissions.aggregate(avg_grade=Avg('grades_received'))['avg_grade'] or 0
        
        # Get notifications
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
        unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()
        
        # Get project type distribution for charts
        project_type_data = []
        for project_type, _ in Project.PROJECT_TYPES:
            count = supervisor_projects.filter(project_type=project_type).count()
            if count > 0:
                project_type_data.append({
                    'type': project_type,
                    'count': count,
                    'color': '#0c768a' if project_type == 'Research' else '#38c786' if project_type == 'Development' else '#f4ba40'
                })
        
        # Get application status distribution for charts
        application_status_data = [
            {'status': 'Applied', 'count': pending_applications, 'color': '#f4ba40'},
            {'status': 'Accepted', 'count': accepted_applications, 'color': '#38c786'},
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
        project_type_json = json.dumps(project_type_data)
        application_status_json = json.dumps(application_status_data)
        grade_ranges_json = json.dumps(grade_ranges)
        
    except Exception as e:
        # If there's an error, provide default values
        print(f"Error in supervisor dashboard: {e}")
        supervisor_projects = Project.objects.filter(supervisor=request.user)
        total_projects = supervisor_projects.count()
        available_projects = 0
        ongoing_projects = 0
        completed_projects = 0
        
        project_applications = Application.objects.filter(project__supervisor=request.user)
        total_applications = project_applications.count()
        pending_applications = project_applications.filter(status='applied').count()
        accepted_applications = project_applications.filter(status='accepted').count()
        declined_applications = project_applications.filter(status='declined').count()
        active_students = 0
        
        # Default values for other data
        assessments_with_submissions = Assessment.objects.none()
        submissions = StudentSubmission.objects.none()
        upcoming_assessments = Assessment.objects.none()
        overdue_assessments = Assessment.objects.none()
        recent_submissions = StudentSubmission.objects.none()
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
        unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()
        average_grade = 0
        
        # Default chart data
        project_type_data = []
        application_status_data = [
            {'status': 'Applied', 'count': pending_applications, 'color': '#f4ba40'},
            {'status': 'Accepted', 'count': accepted_applications, 'color': '#38c786'},
            {'status': 'Declined', 'count': declined_applications, 'color': '#ed5e49'}
        ]
        grade_ranges = [
            {'range': '90-100', 'count': 0, 'color': '#38c786'},
            {'range': '80-89', 'count': 0, 'color': '#0c768a'},
            {'range': '70-79', 'count': 0, 'color': '#f4ba40'},
            {'range': '60-69', 'count': 0, 'color': '#ed5e49'},
            {'range': 'Below 60', 'count': 0, 'color': '#8590a5'}
        ]
        
        project_type_json = json.dumps(project_type_data)
        application_status_json = json.dumps(application_status_data)
        grade_ranges_json = json.dumps(grade_ranges)
    
    context = {
        'supervisor_projects': supervisor_projects,
        'total_projects': total_projects,
        'available_projects': available_projects,
        'ongoing_projects': ongoing_projects,
        'completed_projects': completed_projects,
        
        'project_applications': project_applications,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'accepted_applications': accepted_applications,
        'declined_applications': declined_applications,
        'active_students': active_students,
        
        'assessments': assessments_with_submissions,
        'submissions': submissions,
        'upcoming_assessments': upcoming_assessments,
        'overdue_assessments': overdue_assessments,
        'recent_submissions': recent_submissions,
        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count,
        'average_grade': round(average_grade, 1),
        
        # Chart data
        'project_type_data': project_type_data,
        'application_status_data': application_status_data,
        'grade_ranges': grade_ranges,
        'project_type_json': project_type_json,
        'application_status_json': application_status_json,
        'grade_ranges_json': grade_ranges_json,
    }
    
    return render(request, 'supervisor_dashboard.html', context)
