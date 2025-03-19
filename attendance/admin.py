from django.contrib import admin
from django.contrib import messages
from .models import Group, Profile, Course, Lesson, Semester
from django.contrib.auth.models import User

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'start_date', 'end_date', 'is_active')
    list_filter = ('type', 'is_active')
    search_fields = ['name']

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_students_count')
    search_fields = ['name']
    filter_horizontal = ['students']
    
    def get_students_count(self, obj):
        return obj.students.count()
    get_students_count.short_description = 'Количество студентов'

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "students":
            kwargs["queryset"] = User.objects.filter(profile__role='Студент')
        return super().formfield_for_manytomany(db_field, request, **kwargs)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'student_id')
    list_filter = ('role',)
    search_fields = ['user__username', 'student_id']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'semester')
    list_filter = ('teacher', 'semester')
    search_fields = ['name']

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('course', 'day_of_week')
    list_filter = ('course', 'day_of_week')
    search_fields = ['course__name']
