from django.db import models

from fastydli.base.models import BaseModel


class CustomerModel(BaseModel):

    phone_number = models.CharField(
        max_length=15, blank=True, null=True, default=None)
    customer_profile = models.TextField(blank=True, null=True, default=None)
    # status = models.TextField(blank=True, null=True, default=None)

    def __str__(self):
        return f'{self.id}'

    def __repr__(self):
        return f'CustomerModel(phone_number={self.phone_number}, created_at={self.created_at}, updated_at={self.updated_at})'


class ConversationHistory(BaseModel):

    role = models.CharField(max_length=20, default=None, blank=True, null=True)
    customer = models.ForeignKey(
        CustomerModel, on_delete=models.CASCADE, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    tool_name = models.CharField(max_length=50, blank=True, null=True)
    tool_call_id = models.CharField(max_length=50, blank=True, null=True)
    call_id = models.CharField(max_length=50, blank=True, null=True)
    type = models.CharField(max_length=30, blank=True,
                            null=True, default='message')
    arguments = models.JSONField(null=True, blank=True)
    result = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.id}'

    def __repr__(self):
        return f'ConversationHistory(id={self.id}, role={self.role}, message={self.message}, tool_call_id={self.tool_call_id}, type={self.type}, tool_calls={self.tool_calls}, created_at={self.created_at}, updated_at={self.updated_at})'
