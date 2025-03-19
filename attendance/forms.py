from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, Attendance, Lesson, Course, Group, Semester

class UserRegisterForm(UserCreationForm):
    ROLE_CHOICES = (
        ('student', 'Студент'),
        ('teacher', 'Преподаватель'),
    )
    
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30, required=True, label='Имя')
    last_name = forms.CharField(max_length=30, required=True, label='Фамилия')
    role = forms.ChoiceField(choices=ROLE_CHOICES, label='Роль')
    student_id = forms.CharField(max_length=20, required=False, label='Студенческий билет')
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        student_id = cleaned_data.get('student_id')
        
        if role == 'student' and not student_id:
            self.add_error('student_id', 'Студенческий билет обязателен для студентов')
        
        return cleaned_data

# Форма для создания занятия
class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['course', 'group', 'day_of_week', 'start_time', 'end_time', 'classroom']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

# Форма для отметки посещаемости
class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['student', 'lesson', 'present']

class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = ['name', 'type', 'start_date', 'end_date', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'teacher', 'semester', 'custom_start_date']
        widgets = {
            'custom_start_date': forms.DateInput(attrs={'type': 'date'}),
        }
