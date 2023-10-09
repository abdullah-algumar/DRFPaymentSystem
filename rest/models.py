from datetime import timezone
from django.db import models
from django.contrib.auth.models import User
from utils.models import BaseModel
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email or not password:
            raise ValueError('Verilen e-posta ve şifre ayarlanmalıdır')
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None):
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class CustomUser(AbstractBaseUser):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'

    def has_module_perms(self, app_label):
        return True

    def has_perm(self, perm, obj=None):
        return self.is_staff

    def __str__(self):
        return self.email
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'

class Card(BaseModel):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('PASSIVE', 'Passive'),
        ('DELETED', 'Deleted'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    card_no = models.CharField(max_length=16, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PASSIVE')
    label = models.CharField(max_length=50, default='SYSTEM_CARD')

    def __str__(self):
        return self.card_no

    class Meta:
        db_table = 'card'
        verbose_name = 'Card'


class Transaction(BaseModel):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.description

    class Meta:
        db_table = 'transactions'
        verbose_name = 'Transaction'