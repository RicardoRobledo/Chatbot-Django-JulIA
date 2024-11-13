from django.contrib import admin

from .models import CustomerModel, ConversationHistory


admin.site.register([CustomerModel, ConversationHistory])
