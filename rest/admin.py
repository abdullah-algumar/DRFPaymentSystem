from django.contrib import admin
from rest.models import *

admin.site.register(CustomUser)
admin.site.register(Card)
admin.site.register(Transaction)