from rest_framework import serializers
from rest.models import CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        exclude = ['password', 'is_staff']
        extra_kwargs = {
            'email': {'read_only': True},
            'is_active': {'read_only': True},
            'user_type': {'read_only': True},
        }

class UserRegisterSerializer(serializers.ModelSerializer):
    
    def create(self, validated_data):
        user = CustomUser.objects.create_user(email=validated_data['email'], password=validated_data['password'])
        return user

    class Meta:
        model = CustomUser
        exclude = ['last_login', 'is_active', 'is_staff']
        extra_kwargs = {
            'password': {'write_only': True},
        }