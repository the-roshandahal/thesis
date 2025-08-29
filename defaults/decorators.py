# your_app/decorators.py

from functools import wraps
from django.shortcuts import redirect
from django.conf import settings
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404

def _get_role_for_user(user):
    """Return a simple role string for a given user object."""
    if not user.is_authenticated:
        return None
    # Prioritise superuser
    if user.is_superuser:
        return "admin"
    if user.is_staff:
        return "supervisor"
    return "student"


def _redirect_to_login(request):
    # keep it simple - append next param
    login_url = settings.LOGIN_URL if hasattr(settings, "LOGIN_URL") else "/accounts/login/"
    return redirect(f"{login_url}?next={request.path}")


def is_admin(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _redirect_to_login(request)
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        return render(request, 'error.html')
    return _wrapped


def is_supervisor(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _redirect_to_login(request)
        # superuser should also be allowed (if you want); adjust logic if not
        if request.user.is_superuser or (request.user.is_staff and not request.user.is_superuser):
            return view_func(request, *args, **kwargs)
        return render(request, 'error.html')
    return _wrapped


def is_student(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _redirect_to_login(request)
        if not request.user.is_staff and not request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        return render(request, 'error.html')
    return _wrapped


def role_required(allowed_roles):
    """
    Generic decorator. allowed_roles = ["admin", "supervisor", "student"]
    Example: @role_required(["admin", "supervisor"])
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return _redirect_to_login(request)

            role = _get_role_for_user(request.user)
            if role in allowed_roles:
                return view_func(request, *args, **kwargs)
            return render(request, 'error.html')
        return _wrapped
    return decorator




# @is_admin
# def create_student(request):
#     # admin-only logic
#     return render(request, "admin/create_student.html")


# @is_supervisor
# def create_project(request):
#     # only supervisors (and superuser) allowed
#     return render(request, "projects/create_project.html")


# @is_student
# def submit_assignment(request):
#     # only students
#     return render(request, "assignments/submit.html")


# @role_required(["admin", "supervisor"])  # both allowed
# def grade_assignment(request, submission_id):
#     # logic for grading
#     return render(request, "assignments/grade.html")