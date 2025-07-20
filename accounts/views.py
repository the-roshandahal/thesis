from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.hashers import check_password, make_password
from .models import Admin, Supervisor, Student, User

def login(request):
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
                print('user found:', user.email)
                print('redirecting to home...')
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
