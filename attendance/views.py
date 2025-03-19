from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.generic import ListView, DetailView
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from .models import Profile, Attendance, Lesson, Course, Group, Semester
from .forms import UserRegisterForm, LessonForm, AttendanceForm, SemesterForm
import datetime
import uuid
from django.contrib.auth import logout

def home(request):
    """Главная страница"""
    return render(request, 'attendance/home.html')

def register(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Создаем профиль пользователя
            role = form.cleaned_data.get('role')
            student_id = form.cleaned_data.get('student_id')
            
            Profile.objects.create(
                user=user,
                role=role,
                student_id=student_id if role == 'student' else None
            )
            
            username = form.cleaned_data.get('username')
            messages.success(request, f'Аккаунт создан для {username}! Теперь вы можете войти.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile(request):
    try:
        if hasattr(request.user, 'student'):
            student = request.user.student
            context = {
                'user': request.user,
                'student_info': {
                    'full_name': student.full_name if hasattr(student, 'full_name') else 'Не указано',
                    'group': student.group.name if student.group else 'Группа не указана',
                    'student_id': student.student_id if hasattr(student, 'student_id') else 'Не указан',
                }
            }
        elif hasattr(request.user, 'teacher'):
            teacher = request.user.teacher
            context = {
                'user': request.user,
                'teacher_info': {
                    'full_name': teacher.full_name if hasattr(teacher, 'full_name') else 'Не указано',
                    'department': teacher.department if hasattr(teacher, 'department') else 'Не указано',
                },
                'teacher_groups': teacher.groups.all() if hasattr(teacher, 'groups') else []
            }
        else:
            context = {
                'user': request.user,
                'profile_empty': True,
                'message': 'Профиль не заполнен'
            }
        
        return render(request, 'attendance/profile.html', context)
    except Exception as e:
        context = {
            'user': request.user,
            'profile_empty': True,
            'message': 'Профиль не заполнен'
        }
        return render(request, 'attendance/profile.html', context)

@login_required
def create_lesson(request):
    """Создание занятия (только для преподавателей)"""
    if request.user.profile.role != 'teacher':
        messages.error(request, 'Только преподаватели могут создавать занятия!')
        return redirect('home')
    
    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            # Проверяем, что преподаватель создает занятие только для своего курса
            if lesson.course.teacher != request.user:
                messages.error(request, 'Вы можете создавать занятия только для своих курсов!')
                return redirect('create_lesson')
            
            lesson.save()
            messages.success(request, 'Занятие успешно создано!')
            return redirect('profile')
    else:
        # Предзаполняем форму только курсами текущего преподавателя
        teacher_courses = Course.objects.filter(teacher=request.user)
        form = LessonForm()
        form.fields['course'].queryset = teacher_courses
    
    return render(request, 'attendance/create_lesson.html', {'form': form})

@login_required
def lesson_detail(request, pk):
    """Детальная информация о занятии"""
    lesson = get_object_or_404(Lesson, pk=pk)
    
    # Проверяем права доступа
    if request.user.profile.role == 'teacher' and lesson.course.teacher != request.user:
        messages.error(request, 'У вас нет доступа к этому занятию!')
        return redirect('profile')
    
    attendances = Attendance.objects.filter(lesson=lesson)
    
    context = {
        'lesson': lesson,
        'attendances': attendances
    }
    
    return render(request, 'attendance/lesson_detail.html', context)

@login_required
def generate_qr(request, lesson_id):
    """Генерация QR-кода для занятия (только для преподавателей)"""
    if request.user.profile.role != 'teacher':
        messages.error(request, 'Только преподаватели могут генерировать QR-коды!')
        return redirect('home')
    
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    
    # Проверяем, что преподаватель создает QR только для своего курса
    if lesson.course.teacher != request.user:
        messages.error(request, 'Вы можете генерировать QR-коды только для своих занятий!')
        return redirect('profile')
    
    # Обновляем QR-код
    lesson.unique_id = uuid.uuid4()
    lesson.qr_code = None  # Сбрасываем старый QR-код
    lesson.save()  # При сохранении сработает метод generate_qr_code()
    
    messages.success(request, 'QR-код успешно обновлен!')
    return redirect('lesson_detail', pk=lesson_id)

@login_required
def check_attendance(request, unique_id):
    """Отметка о посещении через QR-код"""
    lesson = get_object_or_404(Lesson, unique_id=unique_id)
    
    # Проверяем, что пользователь - студент
    if request.user.profile.role != 'student':
        messages.error(request, 'Только студенты могут отмечаться на занятиях!')
        return redirect('home')
    
    # Проверяем, что занятие проходит сегодня
    today = datetime.date.today()
    if today.weekday() != lesson.day_of_week:
        messages.warning(request, 'Это занятие не проходит сегодня!')
        return redirect('profile')
    
    # Проверяем, что студент уже не отмечался на этом занятии сегодня
    attendance, created = Attendance.objects.get_or_create(
        student=request.user,
        lesson=lesson,
        date=today,
        defaults={'present': True}
    )
    
    if created:
        messages.success(request, f'Вы успешно отметились на занятии {lesson.course.name}!')
    else:
        messages.info(request, 'Вы уже отмечены на этом занятии!')
    
    return redirect('profile')

@login_required
def student_attendance(request):
    """Просмотр собственной посещаемости (для студентов)"""
    if request.user.profile.role != 'student':
        messages.error(request, 'Эта страница только для студентов!')
        return redirect('home')
    
    attendances = Attendance.objects.filter(student=request.user).order_by('-date')
    
    context = {
        'attendances': attendances
    }
    
    return render(request, 'attendance/student_attendance.html', context)

@login_required
def teacher_courses(request):
    """Просмотр курсов преподавателя"""
    if request.user.profile.role != 'teacher':
        messages.error(request, 'Эта страница только для преподавателей!')
        return redirect('home')
    
    courses = Course.objects.filter(teacher=request.user)
    
    context = {
        'courses': courses
    }
    
    return render(request, 'attendance/teacher_courses.html', context)

def custom_logout(request):
    logout(request)
    return redirect('login')

def api_logout(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'message': 'Successfully logged out'}, status=200)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def group_detail(request, group_id):
    """Детальная информация о группе и управление студентами"""
    group = get_object_or_404(Group, pk=group_id)
    
    # Проверяем права доступа (только преподаватель группы может управлять ею)
    if request.user.profile.role != 'teacher' or not group.course_set.filter(teacher=request.user).exists():
        messages.error(request, 'У вас нет доступа к управлению этой группой!')
        return redirect('profile')
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        action = request.POST.get('action')
        
        if action == 'add':
            try:
                student = User.objects.get(profile__student_id=student_id, profile__role='student')
                if student not in group.students.all():
                    group.students.add(student)
                    messages.success(request, f'Студент {student.username} добавлен в группу.')
                else:
                    messages.warning(request, 'Этот студент уже в группе.')
            except User.DoesNotExist:
                messages.error(request, 'Студент с таким ID не найден.')
        
        elif action == 'remove':
            try:
                student = User.objects.get(id=student_id, profile__role='student')
                group.students.remove(student)
                messages.success(request, f'Студент {student.username} удален из группы.')
            except User.DoesNotExist:
                messages.error(request, 'Студент не найден.')
    
    context = {
        'group': group,
        'students': group.students.all(),
        'all_students': User.objects.filter(profile__role='student')
    }
    
    return render(request, 'attendance/group_detail.html', context)

@login_required
def group_list(request):
    """Список всех групп преподавателя"""
    if request.user.profile.role != 'teacher':
        messages.error(request, 'Только преподаватели могут просматривать группы!')
        return redirect('home')
    
    # Получаем группы, связанные с курсами преподавателя
    teacher_groups = Group.objects.filter(course__teacher=request.user).distinct()
    
    context = {
        'groups': teacher_groups
    }
    
    return render(request, 'attendance/group_list.html', context)

@login_required
def semester_list(request):
    if request.user.profile.role != 'Преподаватель':
        messages.error(request, 'Доступ запрещен')
        return redirect('home')
    
    semesters = Semester.objects.all().order_by('-start_date')
    return render(request, 'attendance/semester_list.html', {'semesters': semesters})

@login_required
def semester_create(request):
    if request.user.profile.role != 'Преподаватель':
        messages.error(request, 'Доступ запрещен')
        return redirect('home')
    
    if request.method == 'POST':
        form = SemesterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Семестр успешно создан!')
            return redirect('semester_list')
    else:
        form = SemesterForm()
    
    return render(request, 'attendance/semester_form.html', {'form': form})

@login_required
def semester_edit(request, pk):
    if request.user.profile.role != 'Преподаватель':
        messages.error(request, 'Доступ запрещен')
        return redirect('home')
    
    semester = get_object_or_404(Semester, pk=pk)
    
    if request.method == 'POST':
        form = SemesterForm(request.POST, instance=semester)
        if form.is_valid():
            form.save()
            messages.success(request, 'Семестр успешно обновлен!')
            return redirect('semester_list')
    else:
        form = SemesterForm(instance=semester)
    
    return render(request, 'attendance/semester_form.html', {
        'form': form,
        'semester': semester
    })
