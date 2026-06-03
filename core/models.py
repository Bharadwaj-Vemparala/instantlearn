import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class CustomUser(AbstractUser):
    ROLE_TEACHER = 'teacher'
    ROLE_STUDENT = 'student'
    ROLE_CHOICES = [
        (ROLE_TEACHER, 'Teacher'),
        (ROLE_STUDENT, 'Student'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_STUDENT)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(blank=True, default='')

    def is_teacher(self):
        return self.role == self.ROLE_TEACHER

    def is_student(self):
        return self.role == self.ROLE_STUDENT

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"


def generate_invite_code():
    return uuid.uuid4().hex[:8].upper()


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    teacher = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE,
        related_name='taught_courses',
        limit_choices_to={'role': 'teacher'}
    )
    students = models.ManyToManyField(
        CustomUser, related_name='enrolled_courses',
        blank=True, limit_choices_to={'role': 'student'}
    )
    invite_code = models.CharField(max_length=8, unique=True, default=generate_invite_code)
    cover_color = models.CharField(max_length=7, default='#2563EB')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def student_count(self):
        return self.students.count()


class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    instructions = models.TextField()
    attachment = models.FileField(upload_to='assignment_attachments/', null=True, blank=True)
    deadline = models.DateTimeField()
    max_marks = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['deadline']

    def __str__(self):
        return f"{self.title} — {self.course.title}"

    def is_overdue(self):
        return timezone.now() > self.deadline

    def submission_count(self):
        return self.submissions.count()


class Submission(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_GRADED = 'graded'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_GRADED, 'Graded'),
    ]
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE,
        related_name='submissions',
        limit_choices_to={'role': 'student'}
    )
    text_content = models.TextField(blank=True, default='')
    file_upload = models.FileField(upload_to='submissions/', null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    graded_marks = models.PositiveIntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True, default='')
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('assignment', 'student')
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student.username} → {self.assignment.title}"

    def grade_percentage(self):
        if self.graded_marks is not None and self.assignment.max_marks > 0:
            return round((self.graded_marks / self.assignment.max_marks) * 100, 1)
        return None


class Attendance(models.Model):
    STATUS_PRESENT = 'present'
    STATUS_ABSENT = 'absent'
    STATUS_CHOICES = [
        (STATUS_PRESENT, 'Present'),
        (STATUS_ABSENT, 'Absent'),
    ]
    student = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE,
        related_name='attendances',
        limit_choices_to={'role': 'student'}
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ABSENT)
    marked_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'course', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.student.username} | {self.course.title} | {self.date} | {self.status}"


class Material(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    file = models.FileField(upload_to='materials/', null=True, blank=True)
    external_link = models.URLField(blank=True, default='')
    module_tag = models.CharField(max_length=100, blank=True, default='General')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.title} — {self.course.title}"

    def is_file(self):
        return bool(self.file)

    def is_link(self):
        return bool(self.external_link)
