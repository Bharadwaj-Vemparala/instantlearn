from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils import timezone
from .models import CustomUser, Course, Assignment, Submission, Attendance, Material


# ─── Auth Forms ───────────────────────────────────────────────────────────────

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(
        attrs={'class': 'form-control', 'placeholder': 'Email address'}
    ))
    first_name = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'First name'}
    ))
    last_name = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Last name'}
    ))
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial=CustomUser.ROLE_STUDENT
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'role', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ('username', 'password1', 'password2'):
            self.fields[field_name].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['placeholder'] = 'Choose a username'
        self.fields['password1'].widget.attrs['placeholder'] = 'Create password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm password'


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })


# ─── Course Forms ──────────────────────────────────────────────────────────────

class CourseCreateForm(forms.ModelForm):
    COVER_COLORS = [
        ('#2563EB', 'Royal Blue'),
        ('#7C3AED', 'Violet'),
        ('#059669', 'Emerald'),
        ('#DC2626', 'Red'),
        ('#D97706', 'Amber'),
        ('#0891B2', 'Cyan'),
    ]
    cover_color = forms.ChoiceField(
        choices=COVER_COLORS,
        widget=forms.RadioSelect(attrs={'class': 'color-radio'}),
        initial='#2563EB'
    )

    class Meta:
        model = Course
        fields = ('title', 'description', 'cover_color')
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Introduction to Machine Learning'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'What will students learn in this course?'
            }),
        }


class CourseEnrollForm(forms.Form):
    invite_code = forms.CharField(
        max_length=8,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center text-uppercase letter-spacing',
            'placeholder': 'Enter 8-character code',
            'maxlength': '8',
            'autocomplete': 'off'
        })
    )

    def clean_invite_code(self):
        code = self.cleaned_data['invite_code'].strip().upper()
        if not Course.objects.filter(invite_code=code).exists():
            raise forms.ValidationError("No course found with this invite code. Please check and try again.")
        return code


# ─── Assignment Forms ──────────────────────────────────────────────────────────

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ('title', 'instructions', 'attachment', 'deadline', 'max_marks')
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Assignment title'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Detailed instructions for students...'
            }),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
            'deadline': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'max_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1, 'max': 1000
            }),
        }

    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if deadline and deadline <= timezone.now():
            raise forms.ValidationError("Deadline must be in the future.")
        return deadline


# ─── Submission Form ───────────────────────────────────────────────────────────

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ('text_content', 'file_upload')
        widgets = {
            'text_content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Write your answer here, or upload a file below...'
            }),
            'file_upload': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        text = cleaned_data.get('text_content', '').strip()
        file = cleaned_data.get('file_upload')
        if not text and not file:
            raise forms.ValidationError("Please provide either text content or a file upload.")
        return cleaned_data


# ─── Grading Form ─────────────────────────────────────────────────────────────

class GradeSubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ('graded_marks', 'feedback')
        widgets = {
            'graded_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': 'Marks awarded'
            }),
            'feedback': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Provide constructive feedback to the student...'
            }),
        }

    def __init__(self, submission=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if submission:
            self.fields['graded_marks'].widget.attrs['max'] = submission.assignment.max_marks

    def clean_graded_marks(self):
        marks = self.cleaned_data.get('graded_marks')
        instance = getattr(self, 'instance', None)
        if instance and marks is not None:
            if marks > instance.assignment.max_marks:
                raise forms.ValidationError(
                    f"Marks cannot exceed {instance.assignment.max_marks}."
                )
        return marks


# ─── Attendance Form ───────────────────────────────────────────────────────────

class AttendanceDateForm(forms.Form):
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        initial=timezone.now().date
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Select Course'
    )

    def __init__(self, teacher=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['course'].queryset = Course.objects.filter(teacher=teacher)


# ─── Material Form ─────────────────────────────────────────────────────────────

class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ('title', 'description', 'file', 'external_link', 'module_tag')
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Resource title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Brief description (optional)'
            }),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'external_link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://...'
            }),
            'module_tag': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Week 1, Module 3, Lecture Notes'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get('file')
        link = cleaned_data.get('external_link', '').strip()
        if not file and not link:
            raise forms.ValidationError("Provide either a file or an external link.")
        return cleaned_data
