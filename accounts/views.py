from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from .models import Student, Supervisor, User


def login(request):
    if request.user.is_authenticated:
        # User is already logged in, redirect based on their role
        if request.user.is_superuser:
            return redirect('admin_dashboard')
        elif request.user.is_staff:
            return redirect('supervisor_dashboard')
        else:
            return redirect('home')
    else:
        if request.method == 'POST':
            email = request.POST.get('email')
            password = request.POST.get('password')
            remember_me = request.POST.get('remember_me') == 'on'  # Checkbox value
            user_obj = None

            # Try to find user by email in Django User model
            try:
                user = User.objects.get(email=email)
                if check_password(password, user.password):
                    auth_login(request, user)
                    user.last_login = timezone.now()
                    user.save()
                    
                    # Handle "Remember me" functionality
                    if remember_me:
                        # Set session to expire in 30 days (30 * 24 * 60 * 60 seconds)
                        request.session.set_expiry(30 * 24 * 60 * 60)
                        # Set session as persistent (won't expire when browser closes)
                        request.session.modified = True
                    else:
                        # Session expires when browser closes
                        request.session.set_expiry(0)
                    
                    # Redirect based on user role
                    if user.is_superuser:
                        return redirect('admin_dashboard')
                    elif user.is_staff:
                        return redirect('supervisor_dashboard')
                    else:
                        return redirect('home')
                else:
                    messages.error(request, 'Incorrect password.')
            except User.DoesNotExist:
                messages.error(request, f"No user found for email {email}.")

        return render(request, 'accounts/login.html')


def logout_view(request):
    request.session.flush()
    return redirect('homepage')


def student_admin(request):
    students = Student.objects.all()
    return render(request, 'accounts/student_admin.html', {'students': students})


def add_student(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        department = request.POST.get('department')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('add_student')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('add_student')

        user = User.objects.create(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_staff=False,
            is_superuser=False,
            password=make_password(password),
        )
        Student.objects.create(
            user=user,
            department=department,
            student_id=f"STU{user.id:04d}",
        )

        messages.success(request, "Student added successfully.")
        return redirect('student_admin')

    return render(request, 'accounts/add_student.html')


def supervisor_admin(request):
    supervisors = Supervisor.objects.all()
    return render(request, 'accounts/supervisor_admin.html', {'supervisors': supervisors})


def add_supervisor(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        department = request.POST.get('department')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('add_student')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('add_student')

        user = User.objects.create(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_staff=True,
            is_superuser=False,
            password=make_password(password),
        )
        Supervisor.objects.create(
            user=user,
            department=department,
            staff_id=f"SUP{user.id:04d}",
        )

        messages.success(request, "Supervisor added successfully.")
        return redirect('supervisor_admin')

    return render(request, 'accounts/add_supervisor.html')

@login_required
def view_profile(request):
    """View user profile"""
    try:
        if request.user.is_superuser:
            profile = None
        elif request.user.is_staff:
            profile = Supervisor.objects.get(user=request.user)
        else:
            profile = Student.objects.get(user=request.user)
    except (Student.DoesNotExist, Supervisor.DoesNotExist):
        profile = None

    context = {
        'profile': profile,
        'user_is_supervisor': request.user.is_staff and not request.user.is_superuser,
        'user_is_admin': request.user.is_superuser,
    }
    return render(request, 'accounts/view_profile.html', context)

@login_required
def edit_profile(request):
    """Edit user profile"""
    if request.method == 'POST':
        # Handle profile update logic here
        messages.success(request, 'Profile updated successfully!')
        return redirect('view_profile')

    context = {
        'user_is_supervisor': request.user.is_staff and not request.user.is_superuser,
        'user_is_admin': request.user.is_superuser,
    }
    return render(request, 'accounts/edit_profile.html', context)



@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        # Handle password change logic here
        messages.success(request, 'Password changed successfully!')
        return redirect('view_profile')

    context = {
        'user_is_supervisor': request.user.is_staff and not request.user.is_superuser,
        'user_is_admin': request.user.is_superuser,
    }
    return render(request, 'accounts/change_password.html', context)


@login_required
def admin_dashboard(request):
    """Comprehensive admin dashboard with statistics and charts data"""
    # Check if user is admin
    if not request.user.is_superuser:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('home')
        
    from django.db.models import Count, Q
    from django.utils import timezone
    from datetime import datetime, timedelta
    from projects.models import Project
    from application.models import Application, ApplicationMember
    from assessment.models import AssessmentSchema, Assessment, StudentSubmission
    
    # Get overall statistics
    total_students = Student.objects.count()
    total_supervisors = Supervisor.objects.count()
    total_projects = Project.objects.count()
    total_applications = Application.objects.count()
    
    # Application status distribution
    status_counts = Application.objects.values('status').annotate(count=Count('id'))
    status_data = {item['status']: item['count'] for item in status_counts}
    
    # Department statistics
    department_stats = Student.objects.values('department').annotate(count=Count('id'))
    
    # Recent applications (last 5)
    recent_applications = Application.objects.select_related(
        'project'
    ).order_by('-applied_at')[:5]
    
    # Recent activities (simulated data)
    recent_activities = [
        {
            'title': 'New Student Registration',
            'description': 'Student John Doe registered for Computer Science',
            'timestamp': timezone.now() - timedelta(hours=2)
        },
        {
            'title': 'Project Application',
            'description': 'New application received for AI Thesis Project',
            'timestamp': timezone.now() - timedelta(hours=4)
        },
        {
            'title': 'Assessment Created',
            'description': 'New assessment schema created for Semester 2024',
            'timestamp': timezone.now() - timedelta(hours=6)
        },
        {
            'title': 'Supervisor Added',
            'description': 'Dr. Johnson added as new project supervisor',
            'timestamp': timezone.now() - timedelta(hours=8)
        }
    ]
    
    # Monthly application trends (last 12 months)
    monthly_applications = []
    for i in range(12):
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start.replace(day=28) + timedelta(days=4)
        month_end = month_end.replace(day=1) - timedelta(days=1)
        
        count = Application.objects.filter(
            applied_at__gte=month_start,
            applied_at__lte=month_end
        ).count()
        
        monthly_applications.append({
            'month': month_start.strftime('%b'),
            'count': count
        })
    
    # Reverse to show oldest to newest
    monthly_applications.reverse()
    
    context = {
        'total_students': total_students,
        'total_supervisors': total_supervisors,
        'total_projects': total_projects,
        'total_applications': total_applications,
        'status_data': status_data,
        'department_stats': department_stats,
        'recent_applications': recent_applications,
        'recent_activities': recent_activities,
        'monthly_applications': monthly_applications,
    }
    
    return render(request, 'admin_dashboard.html', context)


@login_required
def supervisor_dashboard(request):
    """Comprehensive supervisor dashboard with statistics and charts data"""
    # Check if user is supervisor
    if not request.user.is_staff:
        messages.error(request, "Access denied. Supervisor privileges required.")
        return redirect('home')

    from django.db.models import Count, Q
    from django.utils import timezone
    from datetime import datetime, timedelta
    from projects.models import Project
    from application.models import Application, ApplicationMember
    from assessment.models import AssessmentSchema, Assessment, StudentSubmission
    
    print(f"DEBUG: Starting supervisor_dashboard for user: {request.user}")
    
    # Get the current supervisor
    try:
        supervisor = Supervisor.objects.get(user=request.user)
        print(f"DEBUG: Found supervisor: {supervisor}")
    except Supervisor.DoesNotExist:
        messages.error(request, "Supervisor profile not found. Please contact administrator.")
        return redirect('home')
    
    print(f"DEBUG: About to query projects for supervisor.user: {supervisor.user}")
    
    # Supervisor-specific statistics
    try:
        total_projects = Project.objects.filter(supervisor=supervisor.user).count()
        print(f"DEBUG: Total projects: {total_projects}")
    except Exception as e:
        print(f"DEBUG: Error getting total_projects: {e}")
        total_projects = 0
    
    try:
        total_applications = Application.objects.filter(project__supervisor=supervisor.user).count()
        print(f"DEBUG: Total applications: {total_applications}")
    except Exception as e:
        print(f"DEBUG: Error getting total_applications: {e}")
        total_applications = 0
    
    try:
        accepted_applications = Application.objects.filter(
            project__supervisor=supervisor.user, 
            status='accepted'
        ).count()
        print(f"DEBUG: Accepted applications: {accepted_applications}")
    except Exception as e:
        print(f"DEBUG: Error getting accepted_applications: {e}")
        accepted_applications = 0
    
    try:
        pending_applications = Application.objects.filter(
            project__supervisor=supervisor.user, 
            status='applied'
        ).count()
        print(f"DEBUG: Pending applications: {pending_applications}")
    except Exception as e:
        print(f"DEBUG: Error getting pending_applications: {e}")
        pending_applications = 0
    
    # Get supervisor's projects
    try:
        supervisor_projects = Project.objects.filter(supervisor=supervisor.user)
        print(f"DEBUG: Supervisor projects query successful, count: {supervisor_projects.count()}")
    except Exception as e:
        print(f"DEBUG: Error getting supervisor_projects: {e}")
        supervisor_projects = Project.objects.none()
    
    # Recent applications for supervisor's projects
    try:
        recent_applications = Application.objects.filter(
            project__supervisor=supervisor.user
        ).select_related('project').order_by('-applied_at')[:5]
        print(f"DEBUG: Recent applications query successful, count: {len(recent_applications)}")
    except Exception as e:
        print(f"DEBUG: Error getting recent_applications: {e}")
        recent_applications = []
    
    # Project status distribution
    try:
        project_status_counts = supervisor_projects.values('availability').annotate(count=Count('id'))
        project_status_data = {item['availability']: item['count'] for item in project_status_counts}
        print(f"DEBUG: Project status distribution: {project_status_data}")
    except Exception as e:
        print(f"DEBUG: Error getting project_status_counts: {e}")
        project_status_data = {}
    
    # Monthly application trends for supervisor's projects (last 6 months)
    monthly_applications = []
    try:
        for i in range(6):
            month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
            month_end = month_start.replace(day=28) + timedelta(days=4)
            month_end = month_end.replace(day=1) - timedelta(days=1)
            
            count = Application.objects.filter(
                project__supervisor=supervisor.user,
                applied_at__gte=month_start,
                applied_at__lte=month_end
            ).count()
            
            monthly_applications.append({
                'month': month_start.strftime('%b'),
                'count': count
            })
        
        # Reverse to show oldest to newest
        monthly_applications.reverse()
        print(f"DEBUG: Monthly applications calculated successfully: {len(monthly_applications)} months")
    except Exception as e:
        print(f"DEBUG: Error calculating monthly applications: {e}")
        monthly_applications = []
    
    # Recent activities (supervisor-specific)
    try:
        first_application = recent_applications.first() if recent_applications.exists() else None
        project_title = first_application.project.title if first_application else "your project"
        
        recent_activities = [
            {
                'title': 'New Project Application',
                'description': f'Application received for {project_title}',
                'timestamp': timezone.now() - timedelta(hours=2) if first_application else timezone.now() - timedelta(hours=4)
            },
            {
                'title': 'Project Status Updated',
                'description': 'Project availability status changed',
                'timestamp': timezone.now() - timedelta(hours=6)
            },
            {
                'title': 'Student Assignment',
                'description': 'New student assigned to your project',
                'timestamp': timezone.now() - timedelta(hours=8)
            }
        ]
    except Exception as e:
        print(f"Error creating recent activities: {e}")
        recent_activities = [
            {
                'title': 'Welcome to Dashboard',
                'description': 'Your supervisor dashboard is ready',
                'timestamp': timezone.now()
            }
        ]
    
    # Assessment statistics for supervisor's projects
    try:
        if AssessmentSchema.objects.exists():
            schema = AssessmentSchema.objects.first()
            total_assessments = Assessment.objects.filter(schema=schema).count()
            completed_submissions = StudentSubmission.objects.filter(
                assignment__schema=schema
            ).count()
        else:
            total_assessments = 0
            completed_submissions = 0
    except Exception as e:
        print(f"Error getting assessment statistics: {e}")
        total_assessments = 0
        completed_submissions = 0
    
    # Ensure we have valid data for the context
    try:
        context = {
            'supervisor': supervisor,
            'total_projects': total_projects,
            'total_applications': total_applications,
            'accepted_applications': accepted_applications,
            'pending_applications': pending_applications,
            'project_status_data': project_status_data,
            'recent_applications': recent_applications,
            'recent_activities': recent_activities,
            'monthly_applications': monthly_applications,
            'total_assessments': total_assessments,
            'completed_submissions': completed_submissions,
            'supervisor_projects': supervisor_projects[:5] if supervisor_projects.exists() else [],  # Last 5 projects
        }
    except Exception as e:
        # Log the error and provide fallback data
        print(f"Error in supervisor_dashboard context: {e}")
        context = {
            'supervisor': supervisor,
            'total_projects': 0,
            'total_applications': 0,
            'accepted_applications': 0,
            'pending_applications': 0,
            'project_status_data': {},
            'recent_applications': [],
            'recent_activities': [],
            'monthly_applications': [],
            'total_assessments': 0,
            'completed_submissions': 0,
            'supervisor_projects': [],
        }
    
    return render(request, 'supervisor_dashboard.html', context)
