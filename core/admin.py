from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser, Course, Assignment, Submission, Attendance, Material


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = UserAdmin.fieldsets + (
        ('Instant Learn', {'fields': ('role', 'avatar', 'bio')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Instant Learn', {'fields': ('role',)}),
    )


class AssignmentInline(admin.TabularInline):
    model = Assignment
    extra = 0
    fields = ('title', 'deadline', 'max_marks')
    show_change_link = True


class MaterialInline(admin.TabularInline):
    model = Material
    extra = 0
    fields = ('title', 'module_tag', 'file', 'external_link')
    show_change_link = True


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'invite_code', 'student_count_display', 'created_at')
    list_filter = ('teacher',)
    search_fields = ('title', 'invite_code', 'teacher__username')
    readonly_fields = ('invite_code', 'created_at', 'updated_at')
    filter_horizontal = ('students',)
    inlines = [AssignmentInline, MaterialInline]

    def student_count_display(self, obj):
        return obj.students.count()
    student_count_display.short_description = 'Students'


class SubmissionInline(admin.TabularInline):
    model = Submission
    extra = 0
    fields = ('student', 'status', 'graded_marks', 'submitted_at')
    readonly_fields = ('submitted_at',)
    show_change_link = True


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'deadline', 'max_marks', 'submission_count_display', 'is_overdue_display')
    list_filter = ('course__teacher', 'course')
    search_fields = ('title', 'course__title')
    readonly_fields = ('created_at',)
    inlines = [SubmissionInline]

    def submission_count_display(self, obj):
        return obj.submissions.count()
    submission_count_display.short_description = 'Submissions'

    def is_overdue_display(self, obj):
        if obj.is_overdue():
            return format_html('<span style="color:red;">⚠ Overdue</span>')
        return format_html('<span style="color:green;">✓ Active</span>')
    is_overdue_display.short_description = 'Status'


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'status', 'graded_marks', 'submitted_at', 'grade_pct')
    list_filter = ('status', 'assignment__course')
    search_fields = ('student__username', 'assignment__title')
    readonly_fields = ('submitted_at', 'graded_at')

    def grade_pct(self, obj):
        pct = obj.grade_percentage()
        if pct is None:
            return '—'
        color = 'green' if pct >= 60 else 'orange' if pct >= 40 else 'red'
        return format_html(f'<span style="color:{color};font-weight:600;">{pct}%</span>')
    grade_pct.short_description = 'Grade %'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'date', 'status', 'marked_at')
    list_filter = ('status', 'course', 'date')
    search_fields = ('student__username', 'course__title')
    date_hierarchy = 'date'


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'module_tag', 'is_file_display', 'uploaded_at', 'uploaded_by')
    list_filter = ('course', 'module_tag')
    search_fields = ('title', 'course__title')
    readonly_fields = ('uploaded_at',)

    def is_file_display(self, obj):
        if obj.file:
            return format_html('<span style="color:blue;">📄 File</span>')
        return format_html('<span style="color:purple;">🔗 Link</span>')
    is_file_display.short_description = 'Type'
