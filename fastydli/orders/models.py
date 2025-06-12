from django.db import models

from fastydli.base.models import BaseModel
from fastydli.customers.models import CustomerModel


class ProductModel(BaseModel):

    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    description = models.TextField()
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    def __str__(self):
        return self.name


class OrderModel(BaseModel):

    customer = models.ForeignKey(CustomerModel, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    order_product_id = models.ManyToManyField(
        ProductModel, through='OrderProductModel')
    address = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f'Order {self.id} by {self.customer.id}'


class OrderProductModel(BaseModel):

    order = models.ForeignKey(OrderModel, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.quantity} of {self.product.name} in order {self.order.id}'

    def __repr__(self):
        return f'OrderProductModel(order={self.order.id}, product={self.product.name}, quantity={self.quantity})'
