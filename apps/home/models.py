import uuid

from django.db import models
from django.contrib.postgres.fields import JSONField


def upload_banner_location(instance, filename):
    filename = uuid.uuid4().hex + '.jpg'
    return "home/banner/{filename}".format(filename=filename)


def upload_advertisements_location(instance, filename):
    filename = uuid.uuid4().hex + '.jpg'
    return "home/posters/{filename}".format(filename=filename)


class Banner(models.Model):
    title = models.CharField(max_length=255, null=False,  blank=False, verbose_name='Название')
    url = models.CharField(max_length=255, null=False, blank=False, verbose_name='Ссылка')
    image = models.ImageField(upload_to=upload_banner_location, null=True, blank=True, verbose_name='Баннер')
    extra = JSONField(blank=True, null=True, default={}, verbose_name='Дополнительно')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Баннер'
        verbose_name_plural = 'Баннеры'


class Advertisement(models.Model):
    title = models.CharField(max_length=255, null=False,  blank=False, verbose_name='Название')
    url = models.CharField(max_length=255, null=False, blank=False, verbose_name='Ссылка')
    image = models.ImageField(upload_to=upload_advertisements_location, null=True, blank=True, verbose_name='фото')
    extra = JSONField(blank=True, null=True, default={}, verbose_name='Дополнительно')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Объявление'
        verbose_name_plural = 'Объявления'