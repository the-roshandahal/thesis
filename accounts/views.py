from django.utils import timezone
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.hashers import check_password, make_password
from .models import Admin, Supervisor, Student, User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from functools import wraps


def admin_required(view_func):
    """Decorator to check if user is admin (superuser)"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to access this page.")
            return redirect('login')
        if not request.user.is_superuser:
            messages.error(request, "Access denied. Admin privileges required.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def supervisor_required(view_func):
    """Decorator to check if user is supervisor (staff)"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to access this page.")
            return redirect('login')
        if not request.user.is_staff:
            messages.error(request, "Access denied. Supervisor privileges required.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def get_user_type(user):
    """Get user type based on staff and superuser flags"""
    if user.is_superuser:
        return 'admin'
    elif user.is_staff:
        return 'supervisor'
    else:
        return 'student'

def login(request):
    if request.user.is_authenticated:
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
            user_type = request.POST.get('user_type')
            user_obj = None

            # Find the correct user based on user_type
            if user_type == 'admin':
                try:
                    user_obj = Admin.objects.get(user__email=email)
                except Admin.DoesNotExist:
                    user_obj = None

            elif user_type == 'supervisor':
                try:
                    user_obj = Supervisor.objects.get(user__email=email)
                except Supervisor.DoesNotExist:
                    user_obj = None

            elif user_type == 'student':
                try:
                    user_obj = Student.objects.get(user__email=email)
                except Student.DoesNotExist:
                    user_obj = None

            if user_obj:
                user = user_obj.user  # Get the actual Django User object
                if check_password(password, user.password):
                    auth_login(request, user)
                    request.session['user_type'] = user_type
                    user.last_login = timezone.now()
                    user.save()
                    
                    # Redirect based on user type after successful login
                    if user.is_superuser:
                        return redirect('admin_dashboard')
                    elif user.is_staff:
                        return redirect('supervisor_dashboard')
                    else:
                        return redirect('home')
                else:
                    messages.error(request, 'Incorrect password.')
            else:
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
    user = request.user
    user_type = get_user_type(user)
    print('DEBUG:', user, user.is_authenticated, user_type)
    context = {'user': user}
    
    if user_type == 'student':
        profile = Student.objects.get(user=user)
        context['profile'] = profile
        return render(request, 'accounts/view_profile.html', context)
    elif user_type == 'supervisor':
        profile = Supervisor.objects.get(user=user)
        context['profile'] = profile
        return render(request, 'accounts/view_profile.html', context)
    elif user_type == 'admin':
        try:
            profile = Admin.objects.get(user=user)
            context['profile'] = profile
        except Admin.DoesNotExist:
            # If admin profile doesn't exist, create one
            profile = Admin.objects.create(user=user, staff_id=f"ADM{user.id:04d}")
            context['profile'] = profile
        return render(request, 'accounts/view_profile.html', context)
    else:
        messages.error(request, 'Profile viewing is not available for this user type.')
        return redirect('home')

@login_required
def edit_profile(request):
    user = request.user
    user_type = get_user_type(user)

    # Get or create profile based on user type
    if user_type == 'student':
        profile = get_object_or_404(Student, user=user)
    elif user_type == 'supervisor':
        profile = get_object_or_404(Supervisor, user=user)
    elif user_type == 'admin':
        profile, created = Admin.objects.get_or_create(
            user=user,
            defaults={'staff_id': f"ADM{user.id:04d}"}
        )
    else:
        messages.error(request, 'Profile editing is not available for this user type.')
        return redirect('home')

    if request.method == 'POST':
        # Editable user fields
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.address = request.POST.get('address', user.address)
        user.contact = request.POST.get('contact', user.contact)

        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']

        user.save()

        # department and staff_id are read-only — not updated here
        profile.save()

        messages.success(request, 'Profile updated successfully.')
        return redirect('view_profile')

    return render(request, 'accounts/edit_profile.html', {
        'user': user,
        'profile': profile,
        'user_type': user_type
    })



@login_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password != confirm_password:
            messages.error(request, 'New password and confirm password do not match.')
        elif len(new_password) < 8:
            messages.error(request, 'New password must be at least 8 characters long.')
        else:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)  # Keeps user logged in
            messages.success(request, 'Your password has been changed successfully.')
            return redirect('view_profile')

    return render(request, 'accounts/change_password.html')


@admin_required
def admin_dashboard(request):
    """Comprehensive admin dashboard with statistics and charts data"""
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


@supervisor_required
def supervisor_dashboard(request):
    """Comprehensive supervisor dashboard with statistics and charts data"""
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
