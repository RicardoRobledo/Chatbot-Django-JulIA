from django.contrib import admin

from .models import ProductModel, OrderModel, OrderProductModel


admin.site.register([ProductModel, OrderModel, OrderProductModel])
