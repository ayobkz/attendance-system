from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image
import uuid
from django.core.exceptions import ValidationError
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.utils import timezone

# Профиль пользователя для дополнительных полей
class Profile(models.Model):
    ROLE_CHOICES = (
        ('student', 'Студент'),
        ('teacher', 'Преподаватель'),
        ('admin', 'Администратор'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    student_id = models.CharField(max_length=20, blank=True, null=True, unique=True)
    rfid_card = models.CharField(max_length=50, blank=True, null=True, unique=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

# Группа студентов
class Group(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название группы')
    description = models.TextField(blank=True, null=True)
    students = models.ManyToManyField(
        User, 
        related_name='student_groups', 
        blank=True,
        verbose_name='Студенты'
    )
    
    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self):
        return self.name

# Обработчик сигнала для проверки студентов при изменении ManyToMany поля
@receiver(m2m_changed, sender=Group.students.through)
def validate_students(sender, instance, action, pk_set, **kwargs):
    if action == "pre_add":
        # Проверяем только при добавлении новых студентов
        if pk_set:
            non_students = []
            for user_id in pk_set:
                user = User.objects.get(pk=user_id)
                if not hasattr(user, 'profile') or user.profile.role != 'Студент':
                    non_students.append(user.username)
            
            if non_students:
                raise ValidationError(
                    f'Следующие пользователи не являются студентами: {", ".join(non_students)}. '
                    'Пожалуйста, удалите их из списка перед сохранением.'
                )

# Предмет/курс
class Semester(models.Model):
    SEMESTER_TYPES = [
        ('FIRST', 'Первый семестр'),
        ('SECOND', 'Второй семестр'),
        ('SUMMER', 'Летний семестр'),
        ('CUSTOM', 'Индивидуальный период'),
    ]

    name = models.CharField(max_length=100, verbose_name='Название')
    type = models.CharField(
        max_length=10, 
        choices=SEMESTER_TYPES, 
        default='FIRST',
        verbose_name='Тип семестра'
    )
    start_date = models.DateField(verbose_name='Дата начала')
    end_date = models.DateField(verbose_name='Дата окончания')
    is_active = models.BooleanField(default=True, verbose_name='Активный')

    class Meta:
        verbose_name = 'Семестр'
        verbose_name_plural = 'Семестры'

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

    def clean(self):
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError('Дата окончания не может быть раньше даты начала')

class Course(models.Model):
    name = models.CharField(
        max_length=200, 
        verbose_name='Название курса',
        null=True,  # Временно
        blank=True  # Временно
    )
    description = models.TextField(blank=True, null=True)
    teacher = models.ForeignKey(
        'auth.User', 
        on_delete=models.CASCADE, 
        verbose_name='Преподаватель',
        null=True,  # Временно
        blank=True  # Временно
    )
    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        verbose_name='Семестр',
        null=True,  # Временно
        blank=True  # Временно
    )
    custom_start_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name='Индивидуальная дата начала'
    )
    
    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'

    def __str__(self):
        return self.name or 'Без названия'

# Занятие
class Lesson(models.Model):
    DAY_CHOICES = (
        (0, 'Понедельник'),
        (1, 'Вторник'),
        (2, 'Среда'),
        (3, 'Четверг'),
        (4, 'Пятница'),
        (5, 'Суббота'),
        (6, 'Воскресенье'),
    )
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='lessons')
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='lessons')
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    classroom = models.CharField(max_length=100)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    def __str__(self):
        return f"{self.course.name} - {self.group.name} ({self.get_day_of_week_display()})"
    
    def save(self, *args, **kwargs):
        if not self.qr_code:
            self.generate_qr_code()
        super().save(*args, **kwargs)
    
    def generate_qr_code(self):
        server_ip = "10.130.1.142"  # Здесь укажите ваш локальный IP-адрес
        qr_url = f"http://{server_ip}:8000/attendance/check/{self.unique_id}/" 
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        self.qr_code.save(f"qr_{self.course.name}_{self.group.name}.png", 
                          File(buffer), save=False)

# Запись о посещении
class Attendance(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)
    present = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['student', 'lesson', 'date']
    
    def __str__(self):
        status = "Присутствовал" if self.present else "Отсутствовал"
        return f"{self.student.username} - {self.lesson.course.name} - {self.date} - {status}"
