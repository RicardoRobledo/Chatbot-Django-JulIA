from django.db import models

from fastydli.base.models import BaseModel


class CustomerModel(BaseModel):

    first_name = models.CharField(max_length=20, blank=True, null=True)
    last_name = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f'{self.id}'

    def __repr__(self):
        return f'CustomerModel(first_name={self.first_name}, last_name={self.last_name}, created_at={self.created_at}, updated_at={self.updated_at})'


class ConversationHistory(BaseModel):

    role = models.CharField(max_length=20, default=None, blank=True, null=True)
    customer = models.ForeignKey(
        CustomerModel, on_delete=models.CASCADE, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    tool_call_id = models.CharField(max_length=50, blank=True, null=True)
    type = models.CharField(max_length=30, blank=True,
                            null=True, default='message')
    tool_calls = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f'{self.id}'

    def __repr__(self):
        return f'ConversationHistory(id={self.id}, role={self.role}, message={self.message}, tool_call_id={self.tool_call_id}, type={self.type}, tool_calls={self.tool_calls}, created_at={self.created_at}, updated_at={self.updated_at})'
