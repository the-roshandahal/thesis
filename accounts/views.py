from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.db.models import Q
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.hashers import check_password, make_password
from .models import Admin, Supervisor, Student, User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from defaults.decorators import *




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
            return admin_dashboard(request)
        elif request.user.is_staff:
            return render(request, 'supervisor_dashboard.html')
        else:
            return redirect('home')
    else:
        if request.method == 'POST':
            email_or_username = request.POST.get('email')
            password = request.POST.get('password')

            # Find a user by either email or username
            try:
                user = User.objects.get(Q(email=email_or_username) | Q(username=email_or_username))
            except User.DoesNotExist:
                user = None

            if user is not None:
                # Use Django's authenticate function to verify password
                authenticated_user = authenticate(request, username=user.username, password=password)
                
                if authenticated_user is not None:
                    auth_login(request, authenticated_user)
                    messages.success(request, f"Welcome back, {authenticated_user.username}!")
                    return redirect('home')
                else:
                    messages.error(request, 'Invalid password.')
            else:
                messages.error(request, 'No user found with that email or username.')

    return render(request, 'accounts/login.html')


def logout_view(request):
    request.session.flush()
    return redirect('homepage')


@login_required
@is_admin
def student_admin(request):
    students = Student.objects.all()
    return render(request, 'accounts/student_admin.html', {'students': students})


@login_required
@is_admin
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
            username=email.lower(),
            email=email.lower(),
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


@login_required
@is_admin
def supervisor_admin(request):
    supervisors = Supervisor.objects.all()
    return render(request, 'accounts/supervisor_admin.html', {'supervisors': supervisors})


@login_required
@is_admin
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
            username=email.lower(),
            email=email.lower(),
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

@login_required
@is_admin
def admin_dashboard(request):
    """Comprehensive admin dashboard with statistics and charts data"""
    from django.db.models import Count, Q
    from django.utils import timezone
    from datetime import datetime, timedelta
    from projects.models import Project
    from application.models import Application
    from assessment.models import AssessmentSchema, Assessment, StudentSubmission
    
    # Basic counts
    total_students = Student.objects.count()
    total_supervisors = Supervisor.objects.count()
    total_projects = Project.objects.count()
    total_applications = Application.objects.count()
    
    # Application status distribution
    status_counts = Application.objects.values('status').annotate(count=Count('id'))
    status_data = {item['status']: item['count'] for item in status_counts}
    
    # Department statistics
    department_stats = Student.objects.values('department').annotate(count=Count('id')).order_by('-count')
    
    # Recent applications (last 5)
    recent_applications = Application.objects.select_related(
        'project'
    ).order_by('-applied_at')[:5]
    
    # Recent activities (simulated for now)
    recent_activities = [
        {
            'title': 'New Student Registration',
            'description': 'Student John Doe registered in Computer Science department',
            'timestamp': timezone.now() - timedelta(hours=2)
        },
        {
            'title': 'Project Application Submitted',
            'description': 'Application submitted for AI Project by Student Jane Smith',
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
@is_admin
def delete_student(request, user_id):
    student = User.objects.get(id=user_id)
    student.delete()
    messages.success(request,'Student deleted succesfully')
    return redirect(student_admin)



@login_required
@is_admin
def delete_supervisor(request, user_id):
    supervisor = User.objects.get(id=user_id)
    supervisor.delete()
    messages.success(request,'Supervisor deleted succesfully')
    return redirect(supervisor_admin)




@login_required
@is_admin
def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    user = student.user  

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        department = request.POST.get('department')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        # Email uniqueness check (exclude current user)
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, "Email already exists.")
            return redirect('edit_student', student_id=student.id)

        # Password validation (only if provided)
        if password or password2:
            if password != password2:
                messages.error(request, "Passwords do not match.")
                return redirect('edit_student', student_id=student.id)
            user.password = make_password(password)

        # Update user fields
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.username = email
        user.save()

        # Update student fields
        student.department = department
        student.save()

        messages.success(request, "Student updated successfully.")
        return redirect('student_admin')

    context = {
        'student': student,
    }
    return render(request, 'accounts/edit_student.html', context)




@login_required
@is_admin
def edit_supervisor(request, supervisor_id):
    supervisor = get_object_or_404(Supervisor, id=supervisor_id)
    user = supervisor.user  

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        department = request.POST.get('department')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        # Email uniqueness check (exclude current supervisor’s user)
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, "Email already exists.")
            return redirect('edit_supervisor', supervisor_id=supervisor.id)

        # Password validation (only if provided)
        if password or password2:
            if password != password2:
                messages.error(request, "Passwords do not match.")
                return redirect('edit_supervisor', supervisor_id=supervisor.id)
            user.password = make_password(password)

        # Update user fields
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.username = email
        user.save()

        # Update supervisor fields
        supervisor.department = department
        supervisor.save()

        messages.success(request, "Supervisor updated successfully.")
        return redirect('supervisor_admin')  # list page for supervisors

    context = {
        'supervisor': supervisor,
    }
    return render(request, 'accounts/edit_supervisor.html', context)
