# Generated by Django 5.1.7 on 2025-03-23 11:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_hash_existing_passwords'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subjectattendance',
            name='date',
            field=models.DateField(),
        ),
    ]
