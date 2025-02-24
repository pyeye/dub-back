from django.conf import settings
from rest_framework import serializers

from .models import User, Customer, Company, CompanyStatus, Staff


class CustomerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Customer
        fields = ('surname',)


class CompanyStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = CompanyStatus
        fields = ('name', 'coefficient')


class CompanySerializer(serializers.ModelSerializer):
    status = CompanyStatusSerializer(read_only=True)

    class Meta:
        model = Company
        fields = ('name', 'status')


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'email', 'name',  'password', 'phone', 'extra')
        extra_kwargs = {'password': {'write_only': True}}


class StaffSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Staff
        fields = ('id', 'user', 'extra')



class CustomerCompanySerializer(serializers.ModelSerializer):
    profile_object = CompanySerializer()

    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'password', 'is_company', 'phone', 'profile_object', 'extra')
        extra_kwargs = {'password': {'write_only': True}}


    def create(self, validated_data):
        return User.objects.create_company_customer(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.phone = validated_data.get('phone', instance.phone)
        profile_object = validated_data.get('profile_object', None)

        if profile_object is not None:
            instance.profile_object.name = profile_object.get('name', instance.profile_object.name)
            instance.profile_object.save()

        instance.save()

        return instance


class CustomerChangePassSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(max_length=128, write_only=True, required=False)

    class Meta:
        model = User
        fields = ('id', 'password', 'old_password')
        extra_kwargs = {'password': {'write_only': True}}

    def validate_password(self, value):
        old_password = self.initial_data.pop('old_password', None)
        password = self.initial_data.pop('password', None)

        if old_password is None:
            raise serializers.ValidationError('Введите старый пароль')

        if password is None:
            raise serializers.ValidationError('Введите новый пароль')

        if not self.instance.check_password(old_password):
            raise serializers.ValidationError('Неверный старый пароль')

        return value

    def update(self, instance, validated_data):
        password = validated_data.get('password')

        if password is not None:
            instance.set_password(password)

        instance.save()

        return instance

