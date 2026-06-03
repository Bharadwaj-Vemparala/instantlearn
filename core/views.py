import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.utils import timezone
from django.db.models import Avg, Count, Q
from functools import wraps

from .models import CustomUser, Course, Assignment, Submission, Attendance, Material
from .forms import (
    RegisterForm, LoginForm, CourseCreateForm, CourseEnrollForm,
    AssignmentForm, SubmissionForm, GradeSubmissionForm,
    AttendanceDateForm, MaterialForm
)


# ─── Role Decorators ──────────────────────────────────────────────────────────

def teacher_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_teacher():
            messages.error(request, "Access restricted to teachers only.")
            return redirect('student_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def student_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_student():
            messages.error(request, "Access restricted to students only.")
            return redirect('teacher_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─── Auth Views ───────────────────────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Welcome to Instant Learn, {user.first_name}! 🎉")
        return redirect('dashboard')
    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect('dashboard')
    return render(request, 'auth/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You've been logged out. See you soon!")
    return redirect('login')


@login_required
def dashboard_redirect(request):
    if request.user.is_teacher():
        return redirect('teacher_dashboard')
    return redirect('student_dashboard')


# ─── Teacher Views ─────────────────────────────────────────────────────────────

@teacher_required
def teacher_dashboard(request):
    courses = Course.objects.filter(teacher=request.user).annotate(
        student_count=Count('students'),
        assignment_count=Count('assignments')
    )
    total_students = sum(c.student_count for c in courses)
    total_assignments = Assignment.objects.filter(course__teacher=request.user).count()
    pending_grading = Submission.objects.filter(
        assignment__course__teacher=request.user,
        status='pending'
    ).count()
    recent_submissions = Submission.objects.filter(
        assignment__course__teacher=request.user
    ).select_related('student', 'assignment').order_by('-submitted_at')[:5]

    context = {
        'courses': courses,
        'total_students': total_students,
        'total_assignments': total_assignments,
        'pending_grading': pending_grading,
        'recent_submissions': recent_submissions,
    }
    return render(request, 'teacher/dashboard.html', context)


@teacher_required
def course_create(request):
    form = CourseCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        course = form.save(commit=False)
        course.teacher = request.user
        course.save()
        messages.success(request, f"Course '{course.title}' created! Invite code: {course.invite_code}")
        return redirect('teacher_course_detail', pk=course.pk)
    return render(request, 'teacher/course_form.html', {'form': form, 'action': 'Create'})


@teacher_required
def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk, teacher=request.user)
    form = CourseCreateForm(request.POST or None, instance=course)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Course updated successfully.")
        return redirect('teacher_course_detail', pk=course.pk)
    return render(request, 'teacher/course_form.html', {'form': form, 'action': 'Edit', 'course': course})


@teacher_required
def teacher_course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk, teacher=request.user)
    assignments = course.assignments.annotate(sub_count=Count('submissions'))
    students = course.students.all()
    materials = course.materials.all()
    context = {
        'course': course,
        'assignments': assignments,
        'students': students,
        'materials': materials,
    }
    return render(request, 'teacher/course_detail.html', context)


@teacher_required
def assignment_create(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk, teacher=request.user)
    form = AssignmentForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        assignment = form.save(commit=False)
        assignment.course = course
        assignment.save()
        messages.success(request, f"Assignment '{assignment.title}' published!")
        return redirect('teacher_course_detail', pk=course.pk)
    return render(request, 'teacher/assignment_form.html', {
        'form': form, 'course': course, 'action': 'Create'
    })


@teacher_required
def assignment_edit(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, course__teacher=request.user)
    form = AssignmentForm(request.POST or None, request.FILES or None, instance=assignment)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Assignment updated.")
        return redirect('teacher_course_detail', pk=assignment.course.pk)
    return render(request, 'teacher/assignment_form.html', {
        'form': form, 'course': assignment.course, 'action': 'Edit', 'assignment': assignment
    })


@teacher_required
def assignment_submissions(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, course__teacher=request.user)
    submissions = assignment.submissions.select_related('student').order_by('-submitted_at')
    enrolled_students = assignment.course.students.all()
    submitted_ids = set(submissions.values_list('student_id', flat=True))
    not_submitted = enrolled_students.exclude(id__in=submitted_ids)
    avg_marks = submissions.filter(
        graded_marks__isnull=False
    ).aggregate(avg=Avg('graded_marks'))['avg']

    context = {
        'assignment': assignment,
        'submissions': submissions,
        'not_submitted': not_submitted,
        'avg_marks': round(avg_marks, 1) if avg_marks else None,
    }
    return render(request, 'teacher/submissions_list.html', context)


@teacher_required
def grade_submission(request, pk):
    submission = get_object_or_404(Submission, pk=pk, assignment__course__teacher=request.user)
    form = GradeSubmissionForm(submission=submission, instance=submission,
                                data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        sub = form.save(commit=False)
        sub.status = 'graded'
        sub.graded_at = timezone.now()
        sub.save()
        messages.success(request, f"Graded {submission.student.get_full_name() or submission.student.username}'s submission.")
        return redirect('assignment_submissions', pk=submission.assignment.pk)
    return render(request, 'teacher/grade_submission.html', {
        'submission': submission,
        'form': form,
    })


@teacher_required
def attendance_register(request):
    teacher = request.user
    date_form = AttendanceDateForm(teacher=teacher, data=request.GET or None)
    context = {'date_form': date_form, 'attendance_data': None}

    if request.GET and date_form.is_valid():
        course = date_form.cleaned_data['course']
        date = date_form.cleaned_data['date']
        students = course.students.all()
        existing = {
            a.student_id: a for a in Attendance.objects.filter(course=course, date=date)
        }
        attendance_data = []
        for student in students:
            att = existing.get(student.id)
            attendance_data.append({
                'student': student,
                'status': att.status if att else 'absent',
                'attendance_id': att.pk if att else None,
            })
        context.update({
            'course': course,
            'date': date,
            'attendance_data': attendance_data,
        })

    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        date_str = request.POST.get('date')
        course = get_object_or_404(Course, pk=course_id, teacher=teacher)
        from datetime import date as date_type
        import datetime
        att_date = datetime.date.fromisoformat(date_str)
        students = course.students.all()
        for student in students:
            status = request.POST.get(f'status_{student.id}', 'absent')
            Attendance.objects.update_or_create(
                student=student, course=course, date=att_date,
                defaults={'status': status}
            )
        messages.success(request, f"Attendance saved for {att_date.strftime('%B %d, %Y')}.")
        return redirect(f"{request.path}?course={course_id}&date={date_str}")

    return render(request, 'teacher/attendance_register.html', context)


@teacher_required
def material_upload(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk, teacher=request.user)
    form = MaterialForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        material = form.save(commit=False)
        material.course = course
        material.uploaded_by = request.user
        material.save()
        messages.success(request, f"'{material.title}' uploaded to Resource Vault.")
        return redirect('teacher_course_detail', pk=course.pk)
    return render(request, 'teacher/material_form.html', {'form': form, 'course': course})


@teacher_required
def live_classroom_teacher(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk, teacher=request.user)
    students = course.students.all()
    return render(request, 'teacher/live_classroom.html', {
        'course': course, 'students': students
    })


# ─── Student Views ─────────────────────────────────────────────────────────────

@student_required
def student_dashboard(request):
    student = request.user
    enrolled_courses = student.enrolled_courses.annotate(
        assignment_count=Count('assignments')
    )
    upcoming_assignments = Assignment.objects.filter(
        course__in=enrolled_courses,
        deadline__gte=timezone.now()
    ).order_by('deadline')[:5]
    recent_grades = Submission.objects.filter(
        student=student,
        status='graded'
    ).select_related('assignment', 'assignment__course').order_by('-graded_at')[:5]
    total_assignments = Assignment.objects.filter(course__in=enrolled_courses).count()
    submitted_count = Submission.objects.filter(student=student).count()

    context = {
        'enrolled_courses': enrolled_courses,
        'upcoming_assignments': upcoming_assignments,
        'recent_grades': recent_grades,
        'total_assignments': total_assignments,
        'submitted_count': submitted_count,
    }
    return render(request, 'student/dashboard.html', context)


@student_required
def enroll_course(request):
    form = CourseEnrollForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        code = form.cleaned_data['invite_code']
        course = Course.objects.get(invite_code=code)
        if request.user in course.students.all():
            messages.warning(request, f"You're already enrolled in '{course.title}'.")
        else:
            course.students.add(request.user)
            messages.success(request, f"Enrolled in '{course.title}' successfully! 🎓")
        return redirect('student_dashboard')
    return render(request, 'student/enroll.html', {'form': form})


@student_required
def student_course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.user not in course.students.all():
        messages.error(request, "You are not enrolled in this course.")
        return redirect('student_dashboard')
    assignments = course.assignments.all()
    my_submissions = {
        s.assignment_id: s for s in Submission.objects.filter(
            student=request.user, assignment__course=course
        )
    }
    materials = course.materials.all()
    assignment_data = []
    for a in assignments:
        assignment_data.append({
            'assignment': a,
            'submission': my_submissions.get(a.pk),
        })
    context = {
        'course': course,
        'assignment_data': assignment_data,
        'materials': materials,
    }
    return render(request, 'student/course_detail.html', context)


@student_required
def submit_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    course = assignment.course
    if request.user not in course.students.all():
        raise Http404
    existing_submission = Submission.objects.filter(
        assignment=assignment, student=request.user
    ).first()
    if existing_submission:
        messages.warning(request, "You've already submitted this assignment.")
        return redirect('student_course_detail', pk=course.pk)
    if assignment.is_overdue():
        messages.error(request, "This assignment deadline has passed.")
        return redirect('student_course_detail', pk=course.pk)

    form = SubmissionForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        submission = form.save(commit=False)
        submission.assignment = assignment
        submission.student = request.user
        submission.save()
        messages.success(request, "Submission received! Your teacher will grade it soon.")
        return redirect('student_course_detail', pk=course.pk)
    return render(request, 'student/submit_assignment.html', {
        'assignment': assignment,
        'course': course,
        'form': form,
    })


@student_required
def student_grades(request):
    student = request.user
    submissions = Submission.objects.filter(
        student=student
    ).select_related('assignment', 'assignment__course').order_by('-submitted_at')

    course_stats = {}
    for sub in submissions:
        c = sub.assignment.course
        if c.pk not in course_stats:
            course_stats[c.pk] = {
                'course': c,
                'total': 0,
                'graded': 0,
                'earned': 0,
                'max': 0
            }
        course_stats[c.pk]['total'] += 1
        if sub.status == 'graded' and sub.graded_marks is not None:
            course_stats[c.pk]['graded'] += 1
            course_stats[c.pk]['earned'] += sub.graded_marks
            course_stats[c.pk]['max'] += sub.assignment.max_marks

    for stat in course_stats.values():
        if stat['max'] > 0:
            stat['percentage'] = round((stat['earned'] / stat['max']) * 100, 1)
        else:
            stat['percentage'] = 0

    context = {
        'submissions': submissions,
        'course_stats': list(course_stats.values()),
    }
    return render(request, 'student/grades.html', context)


@student_required
def student_attendance(request):
    student = request.user
    courses = student.enrolled_courses.all()
    attendance_by_course = []
    for course in courses:
        records = Attendance.objects.filter(student=student, course=course)
        total = records.count()
        present = records.filter(status='present').count()
        percentage = round((present / total) * 100, 1) if total > 0 else 0
        attendance_by_course.append({
            'course': course,
            'total': total,
            'present': present,
            'absent': total - present,
            'percentage': percentage,
        })
    context = {
        'attendance_by_course': attendance_by_course,
    }
    return render(request, 'student/attendance.html', context)


@student_required
def student_materials(request):
    student = request.user
    courses = student.enrolled_courses.all()
    materials_by_course = []
    for course in courses:
        mats = course.materials.all()
        if mats.exists():
            materials_by_course.append({'course': course, 'materials': mats})
    return render(request, 'student/materials.html', {
        'materials_by_course': materials_by_course
    })


@student_required
def live_classroom_student(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk)
    if request.user not in course.students.all():
        raise Http404
    return render(request, 'student/live_classroom.html', {'course': course})
