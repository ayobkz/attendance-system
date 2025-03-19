from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Profile

@receiver(pre_save, sender=Profile)
def remove_from_groups_if_not_student(sender, instance, **kwargs):
    try:
        # Получаем старый профиль из базы данных
        old_profile = Profile.objects.get(id=instance.id)
        # Если роль меняется со студента на что-то другое
        if old_profile.role == 'Студент' and instance.role != 'Студент':
            # Удаляем пользователя из всех групп
            instance.user.student_groups.clear()
    except Profile.DoesNotExist:
        # Если это новый профиль, ничего не делаем
        pass 