from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('lesson/new/', views.create_lesson, name='create_lesson'),
    path('lesson/<int:pk>/', views.lesson_detail, name='lesson_detail'),
    path('lesson/<int:lesson_id>/qr/', views.generate_qr, name='generate_qr'),
    path('attendance/check/<uuid:unique_id>/', views.check_attendance, name='check_attendance'),
    path('attendance/student/', views.student_attendance, name='student_attendance'),
    path('courses/teacher/', views.teacher_courses, name='teacher_courses'),
    path('api/logout/', views.api_logout, name='api_logout'),
    path('groups/', views.group_list, name='group_list'),
    path('groups/<int:group_id>/', views.group_detail, name='group_detail'),
    path('semesters/', views.semester_list, name='semester_list'),
    path('semesters/create/', views.semester_create, name='semester_create'),
    path('semesters/<int:pk>/edit/', views.semester_edit, name='semester_edit'),
]
