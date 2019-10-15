from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField, JSONField

from .managers import UserManager, StaffManager, CustomerManager


DEFAULT_COMPANY_STATUS_ID = 2

class PermissionsMixin(models.Model):
    """
    A mixin class that adds the fields and methods necessary to support
    Django"s Permission model using the ModelBackend.
    """
    is_superuser = True

    class Meta:
        abstract = True

    def has_perm(self, perm, obj=None):
        """
        Returns True if the user is superadmin and is active
        """
        return self.is_active and self.is_superuser

    def has_perms(self, perm_list, obj=None):
        """
        Returns True if the user is superadmin and is active
        """
        return self.is_active and self.is_superuser

    def has_module_perms(self, app_label):
        """
        Returns True if the user is superadmin and is active
        """
        return self.is_active and self.is_superuser

    @property
    def is_staff(self):
        return True

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, null=False, blank=False, unique=True, verbose_name='Почта')
    name = models.CharField(max_length=64, null=False, blank=False, verbose_name='Имя')
    date_joined = models.DateField(auto_now_add=True, editable=False, verbose_name='Дата регистрации')
    is_active = models.BooleanField(default=True, editable=False, verbose_name='Активирован')
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name='Телефон')
    scopes = ArrayField(models.CharField(max_length=32), editable=False, verbose_name='Права доступа')
    extra = JSONField(blank=True, null=True, default=None, verbose_name='extra')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


    def __str__(self):
        return self.email

    def get_short_name(self):
        return self.email

    def get_full_name(self):
        return self.email

    @property
    def is_staff(self):
        return True


class Staff(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='staff')
    extra = JSONField(blank=True, null=True, default=None, verbose_name='extra')

    objects = StaffManager()

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'


class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer')
    surname = models.CharField(max_length=30, blank=True, null=True, default=None, verbose_name='Фамилия')
    extra = JSONField(blank=True, null=True, default=None, verbose_name='extra')

    objects = CustomerManager()

    class Meta:
        verbose_name = 'Покупатель'
        verbose_name_plural = 'Покупатели'


class Company(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='company')
    name = models.CharField(max_length=30, null=False, blank=False, verbose_name='Название')
    status = models.ForeignKey('CompanyStatus', on_delete=models.CASCADE, default=DEFAULT_COMPANY_STATUS_ID, related_name='status', null=False, blank=False, verbose_name='Статус')
    extra = JSONField(blank=True, null=True, default=None, verbose_name='extra')

    class Meta:
        verbose_name = 'Юр лицо'
        verbose_name_plural = 'Юр лица'


    def __str__(self):
        return self.name


class CompanyStatus(models.Model):
    name = models.CharField(max_length=30, null=False, blank=False, verbose_name='Имя')
    coefficient = models.DecimalField(null=False, blank=False, verbose_name='Коэффициент', max_digits=4, decimal_places=2)
    extra = JSONField(blank=True, null=True, default=None, verbose_name='extra')

    class Meta:
        verbose_name = 'Статус юр лица'
        verbose_name_plural = 'Статусы юр лица'


    def __str__(self):
        return self.name












