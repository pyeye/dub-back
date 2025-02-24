from django.contrib.auth.models import BaseUserManager
from django.apps import apps
from django.db import models

CUSTOMER_SCOPES = ['customer']
COMPANY_SCOPES = ['customer', 'company']
STAFF_SCOPES = ['customer', 'company', 'staff']
ADMIN_SCOPES = ['customer', 'company', 'staff', 'admin']


class UserManager(BaseUserManager):

    def create_customer(self,  email, profile_object,  password=None, **extra_fields):
        user_model = apps.get_model(app_label='users', model_name='Individual')
        extra_fields['profile_object'] = user_model.objects.create(**profile_object)
        return self._make_user(
            email=email,
            password=password,
            scopes=CUSTOMER_SCOPES,
            **extra_fields,
        )

    def create_company(self, email, profile_object, password=None, **extra_fields):
        company_model = apps.get_model(app_label='users', model_name='Company')
        extra_fields['profile_object'] = company_model.objects.create(**profile_object)
        return self._make_user(
            email=email,
            password=password,
            is_company=True,
            scopes=COMPANY_SCOPES,
            **extra_fields,
        )

    def create_superuser(self, email, password=None, **extra_fields):
        super_user = self._make_user(
            email=email,
            password=password,
            scopes=ADMIN_SCOPES,
            **extra_fields
        )
        user_model = apps.get_model(app_label='users', model_name='Staff')
        return user_model.objects.create(user=super_user)

    def create_staff_user(self, email, password=None, **extra_fields):
        user_model = apps.get_model(app_label='users', model_name='Individual')
        extra_fields['profile_object'] = user_model.objects.create(surname='')
        return self._make_user(
            email=email,
            password=password,
            scopes=STAFF_SCOPES,
            **extra_fields
        )

    def _make_user(self, email, password, scopes, **extra_fields):
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.scopes = scopes
        user.save()

        return user


class CustomerManager(models.Manager):

    def create_customer(self,  email,  password=None, **extra_fields):
        customer = self.model(**extra_fields)
        customer.save()
        customer.user.model(
            email=email,
            scopes=CUSTOMER_SCOPES,
            **extra_fields
        )
        customer.user.set_password(password)
        customer.user.save()


class StaffManager(models.Manager):

    def create_company(self,  email,  password=None, **extra_fields):
        staff = self.model(**extra_fields)
        staff.save()
        staff.user.model(
            email=email,
            scopes=CUSTOMER_SCOPES,
            **extra_fields
        )
        staff.user.set_password(password)
        staff.user.save()



