from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Avg, Q
from django.contrib.auth import get_user_model
from application.models import Application
from projects.models import Project
from assessment.models import Assessment, StudentSubmission, AssessmentSchema
from .models import Notification
import json

# Get the User model (either custom or default)
User = get_user_model()


@login_required
def student_dashboard(request):
    """Student dashboard view with statistics, charts, and project information."""
    try:
        # Get current date
        today = timezone.now().date()
        
        # Get applications for this student
        applications = Application.objects.filter(members__user=request.user).select_related('project')
        total_applications = applications.count()
        has_active_project = applications.filter(status='accepted').exists()
        pending_applications = applications.filter(status='applied').count()
        declined_applications = applications.filter(status='declined').count()
        
        # Get accepted applications to find submissions
        accepted_applications = applications.filter(status='accepted')
        
        # Get submissions for accepted applications
        submissions = StudentSubmission.objects.filter(
            application__in=accepted_applications
        ).select_related('assignment', 'application', 'submitted_by')
        
        # Get ALL assessments for accepted projects
        accepted_project_ids = accepted_applications.values_list('project_id', flat=True)
        all_assessments = Assessment.objects.filter(
            project__in=accepted_project_ids
        ).distinct()
        
        # Get IDs of already submitted assessments
        submitted_assessment_ids = submissions.values_list('assignment_id', flat=True)
        
        # Get upcoming assessments (due in next 30 days) that haven't been submitted yet
        upcoming_assessments = all_assessments.exclude(
            id__in=submitted_assessment_ids
        ).filter(
            due_date__gte=today,
            due_date__lte=today + timezone.timedelta(days=30)
        ).order_by('due_date')
        
        # Get overdue assessments (unsubmitted assessments past due date)
        overdue_assessments = all_assessments.exclude(
            id__in=submitted_assessment_ids
        ).filter(due_date__lt=today)
        
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
            {'status': 'Accepted', 'count': 1 if has_active_project else 0, 'color': '#38c786'},
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
        has_active_project = applications.filter(status='accepted').exists()
        pending_applications = applications.filter(status='applied').count()
        declined_applications = applications.filter(status='declined').count()
        
        # Default values for other data
        accepted_applications = applications.filter(status='accepted')
        submissions = StudentSubmission.objects.none()
        all_assessments = Assessment.objects.none()
        upcoming_assessments = Assessment.objects.none()
        overdue_assessments = Assessment.objects.none()
        recent_submissions = StudentSubmission.objects.none()
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
        unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()
        average_grade = 0
        
        # Default chart data
        application_status_data = [
            {'status': 'Applied', 'count': pending_applications, 'color': '#f4ba40'},
            {'status': 'Accepted', 'count': 1 if has_active_project else 0, 'color': '#38c786'},
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
        'has_active_project': has_active_project,
        'pending_applications': pending_applications,
        'declined_applications': declined_applications,
        
        'assessments': all_assessments,
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
        taken_projects = supervisor_projects.filter(availability='taken').count()
        # For now, we'll treat 'taken' as ongoing until we have more specific statuses
        ongoing_projects = taken_projects
        completed_projects = 0  # No completed status exists yet
        
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


@login_required
def admin_dashboard(request):
    """Admin dashboard view with comprehensive system statistics and management tools."""
    try:
        from datetime import datetime, timedelta
        
        # Get current date
        today = timezone.now().date()
        
        # Basic statistics
        total_students = User.objects.filter(is_staff=False, is_superuser=False).count()
        total_supervisors = User.objects.filter(is_staff=True, is_superuser=False).count()
        total_projects = Project.objects.count()
        total_applications = Application.objects.count()
        
        # Project statistics
        available_projects = Project.objects.filter(availability='available').count()
        taken_projects = Project.objects.filter(availability='taken').count()
        # For now, we'll treat 'taken' as ongoing until we have more specific statuses
        ongoing_projects = taken_projects
        completed_projects = 0  # No completed status exists yet
        
        # Application statistics
        pending_applications = Application.objects.filter(status='applied').count()
        accepted_applications = Application.objects.filter(status='accepted').count()
        declined_applications = Application.objects.filter(status='declined').count()
        
        # Assessment statistics
        total_assessments = Assessment.objects.count()
        total_submissions = StudentSubmission.objects.count()
        graded_submissions = StudentSubmission.objects.filter(grades_received__isnull=False).count()
        pending_grading = total_submissions - graded_submissions
        
        # Recent data
        recent_applications = Application.objects.select_related('project').prefetch_related('members__user').order_by('-applied_at')[:10]
        recent_submissions = StudentSubmission.objects.select_related('assignment', 'application', 'submitted_by').order_by('-submitted_at')[:10]
        recent_projects = Project.objects.select_related('supervisor').order_by('-created')[:5]
        
        # Notifications
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
        unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()
        
        # Calculate trends (last 30 days vs previous 30 days)
        last_30_days = today - timedelta(days=30)
        last_60_days = today - timedelta(days=60)
        
        current_period_apps = Application.objects.filter(applied_at__gte=last_30_days).count()
        previous_period_apps = Application.objects.filter(applied_at__gte=last_60_days, applied_at__lt=last_30_days).count()
        apps_trend = ((current_period_apps - previous_period_apps) / max(previous_period_apps, 1)) * 100 if previous_period_apps > 0 else 0
        
        current_period_subs = StudentSubmission.objects.filter(submitted_at__gte=last_30_days).count()
        previous_period_subs = StudentSubmission.objects.filter(submitted_at__gte=last_60_days, submitted_at__lt=last_30_days).count()
        subs_trend = ((current_period_subs - previous_period_subs) / max(previous_period_subs, 1)) * 100 if previous_period_subs > 0 else 0
        
        # Chart data preparation
        # Application status distribution
        application_status_data = [
            {'status': 'Applied', 'count': pending_applications, 'color': '#f4ba40'},
            {'status': 'Accepted', 'count': accepted_applications, 'color': '#38c786'},
            {'status': 'Declined', 'count': declined_applications, 'color': '#ed5e49'}
        ]
        
        # Project type distribution
        project_types_data = []
        if hasattr(Project, 'PROJECT_TYPES'):
            for project_type, _ in Project.PROJECT_TYPES:
                count = Project.objects.filter(project_type=project_type).count()
                if count > 0:
                    project_types_data.append({
                        'type': project_type,
                        'count': count,
                        'color': '#0c768a' if project_type == 'Research' else '#38c786' if project_type == 'Development' else '#f4ba40'
                    })
        
        # Grade distribution for all submissions
        graded_subs = StudentSubmission.objects.filter(grades_received__isnull=False)
        grade_ranges = [
            {'range': '90-100', 'count': graded_subs.filter(grades_received__gte=90).count(), 'color': '#38c786'},
            {'range': '80-89', 'count': graded_subs.filter(grades_received__gte=80, grades_received__lt=90).count(), 'color': '#0c768a'},
            {'range': '70-79', 'count': graded_subs.filter(grades_received__gte=70, grades_received__lt=80).count(), 'color': '#f4ba40'},
            {'range': '60-69', 'count': graded_subs.filter(grades_received__gte=60, grades_received__lt=70).count(), 'color': '#ed5e49'},
            {'range': 'Below 60', 'count': graded_subs.filter(grades_received__lt=60).count(), 'color': '#8590a5'}
        ]
        
        # Monthly applications for trend chart (last 6 months)
        monthly_applications = []
        for i in range(6):
            month_start = today.replace(day=1) - timedelta(days=i*30)
            month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            
            count = Application.objects.filter(
                applied_at__date__gte=month_start,
                applied_at__date__lte=month_end
            ).count()
            
            monthly_applications.append({
                'month': month_start.strftime('%b %Y'),
                'count': count
            })
        
        monthly_applications.reverse()  # Show chronologically
        
        # Convert to JSON for JavaScript
        application_status_json = json.dumps(application_status_data)
        project_types_json = json.dumps(project_types_data)
        grade_ranges_json = json.dumps(grade_ranges)
        monthly_applications_json = json.dumps(monthly_applications)
        
        # Average grade calculation
        average_grade = graded_subs.aggregate(avg_grade=Avg('grades_received'))['avg_grade'] or 0
        
    except Exception as e:
        # If there's an error, provide default values
        print(f"Error in admin dashboard: {e}")
        
        # Basic counts with error handling
        try:
            total_students = User.objects.filter(is_staff=False, is_superuser=False).count()
            total_supervisors = User.objects.filter(is_staff=True, is_superuser=False).count()
            total_projects = Project.objects.count()
            total_applications = Application.objects.count()
        except:
            total_students = total_supervisors = total_projects = total_applications = 0
        
        # Default values for other data
        available_projects = ongoing_projects = completed_projects = 0
        pending_applications = accepted_applications = declined_applications = 0
        total_assessments = total_submissions = graded_submissions = pending_grading = 0
        apps_trend = subs_trend = 0
        average_grade = 0
        
        recent_applications = Application.objects.none()
        recent_submissions = StudentSubmission.objects.none()
        recent_projects = Project.objects.none()
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
        unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()
        
        # Default chart data
        application_status_data = [
            {'status': 'Applied', 'count': 0, 'color': '#f4ba40'},
            {'status': 'Accepted', 'count': 0, 'color': '#38c786'},
            {'status': 'Declined', 'count': 0, 'color': '#ed5e49'}
        ]
        project_types_data = []
        grade_ranges = [
            {'range': '90-100', 'count': 0, 'color': '#38c786'},
            {'range': '80-89', 'count': 0, 'color': '#0c768a'},
            {'range': '70-79', 'count': 0, 'color': '#f4ba40'},
            {'range': '60-69', 'count': 0, 'color': '#ed5e49'},
            {'range': 'Below 60', 'count': 0, 'color': '#8590a5'}
        ]
        monthly_applications = []
        
        application_status_json = json.dumps(application_status_data)
        project_types_json = json.dumps(project_types_data)
        grade_ranges_json = json.dumps(grade_ranges)
        monthly_applications_json = json.dumps(monthly_applications)
    
    context = {
        # Basic statistics
        'total_students': total_students,
        'total_supervisors': total_supervisors,
        'total_projects': total_projects,
        'total_applications': total_applications,
        
        # Project statistics
        'available_projects': available_projects,
        'ongoing_projects': ongoing_projects,
        'completed_projects': completed_projects,
        
        # Application statistics
        'pending_applications': pending_applications,
        'accepted_applications': accepted_applications,
        'declined_applications': declined_applications,
        
        # Assessment statistics
        'total_assessments': total_assessments,
        'total_submissions': total_submissions,
        'graded_submissions': graded_submissions,
        'pending_grading': pending_grading,
        'average_grade': round(average_grade, 1),
        
        # Trends
        'apps_trend': round(apps_trend, 1),
        'subs_trend': round(subs_trend, 1),
        
        # Recent data
        'recent_applications': recent_applications,
        'recent_submissions': recent_submissions,
        'recent_projects': recent_projects,
        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count,
        
        # Chart data
        'application_status_data': application_status_data,
        'project_types_data': project_types_data,
        'grade_ranges': grade_ranges,
        'monthly_applications': monthly_applications,
        'application_status_json': application_status_json,
        'project_types_json': project_types_json,
        'grade_ranges_json': grade_ranges_json,
        'monthly_applications_json': monthly_applications_json,
    }
    
    return render(request, 'admin_dashboard.html', context)
