from django.urls import path
from . import views

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────
    path('',               views.dashboard_redirect,   name='home'),
    path('register/',      views.register_view,         name='register'),
    path('login/',         views.login_view,             name='login'),
    path('logout/',        views.logout_view,            name='logout'),
    path('dashboard/',     views.dashboard_redirect,     name='dashboard'),

    # ── Teacher ───────────────────────────────────────────
    path('teacher/',                                    views.teacher_dashboard,       name='teacher_dashboard'),
    path('teacher/courses/new/',                        views.course_create,           name='course_create'),
    path('teacher/courses/<int:pk>/',                   views.teacher_course_detail,   name='teacher_course_detail'),
    path('teacher/courses/<int:pk>/edit/',              views.course_edit,             name='course_edit'),
    path('teacher/courses/<int:course_pk>/assignments/new/',
                                                        views.assignment_create,       name='assignment_create'),
    path('teacher/assignments/<int:pk>/edit/',          views.assignment_edit,         name='assignment_edit'),
    path('teacher/assignments/<int:pk>/submissions/',   views.assignment_submissions,  name='assignment_submissions'),
    path('teacher/submissions/<int:pk>/grade/',         views.grade_submission,        name='grade_submission'),
    path('teacher/attendance/',                         views.attendance_register,     name='attendance_register'),
    path('teacher/courses/<int:course_pk>/materials/new/',
                                                        views.material_upload,         name='material_upload'),
    path('teacher/courses/<int:course_pk>/live/',       views.live_classroom_teacher,  name='live_classroom_teacher'),

    # ── Student ───────────────────────────────────────────
    path('student/',                                    views.student_dashboard,       name='student_dashboard'),
    path('student/enroll/',                             views.enroll_course,           name='enroll_course'),
    path('student/courses/<int:pk>/',                   views.student_course_detail,   name='student_course_detail'),
    path('student/assignments/<int:pk>/submit/',        views.submit_assignment,       name='submit_assignment'),
    path('student/grades/',                             views.student_grades,          name='student_grades'),
    path('student/attendance/',                         views.student_attendance,      name='student_attendance'),
    path('student/materials/',                          views.student_materials,       name='student_materials'),
    path('student/courses/<int:course_pk>/live/',       views.live_classroom_student,  name='live_classroom_student'),
]
