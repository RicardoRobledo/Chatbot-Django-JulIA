# Generated by Django 5.1.1 on 2025-06-12 22:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_alter_productmodel_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordermodel',
            name='address',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
