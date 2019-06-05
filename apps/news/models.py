import uuid

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils import dateformat
from django.conf import settings


def upload_location(instance, filename):
    filename = uuid.uuid4().hex + '.jpg'
    return "news/{0}".format(filename)


class News(models.Model):
    title = models.CharField(max_length=255, null=False, blank=False, verbose_name='Заголовок')
    description = models.TextField(null=False, blank=False, verbose_name='Описание')
    category = models.ForeignKey('Category', related_name='news', verbose_name='Категория')
    image = models.OneToOneField('NewsImage', on_delete=models.SET_NULL, blank=True, null=True, verbose_name='фото', related_name='news')
    created_at = models.DateField(auto_now_add=True, null=False, blank=True, verbose_name='Созданно')
    updated_at = models.DateField(auto_now=True, null=False, blank=True, verbose_name='Обновленно')
    is_active = models.BooleanField(default=True, null=False, blank=True, verbose_name='Активировано')
    extra = JSONField(blank=True, null=True, default={}, verbose_name='Дополнительно')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
        ordering = ['-updated_at']

    @property
    def date_created(self):
        date = self.format_date(self.created_at)

        return date

    @property
    def date_updated(self):
        date = self.format_date(self.updated_at)

        return date

    @property
    def is_updated(self):
        return self.updated_at > self.created_at

    @staticmethod
    def format_date(date):
        formatted_date = dateformat.format(date, settings.DATE_FORMAT).split()
        return {
            'day': formatted_date[0],
            'month': formatted_date[1],
            'year': formatted_date[2],
        }


class Category(models.Model):
    name = models.CharField(max_length=255, null=False, unique=True, blank=False, verbose_name='Название')
    slug = models.CharField(max_length=128, null=False, unique=True, blank=False, verbose_name='Код')
    is_active = models.BooleanField(null=False, blank=True, default=True, verbose_name='Активированно')
    extra = JSONField(blank=True, null=True, default={}, verbose_name='Дополнительно')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class NewsImage(models.Model):
    src = models.ImageField(upload_to=upload_location, null=True, blank=True, verbose_name='Фото')
    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=True, verbose_name='Созданно')
    extra = JSONField(blank=True, null=True, default={}, verbose_name='Дополнительно')
