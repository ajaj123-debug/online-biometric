# Generated by Django 5.1.7 on 2025-03-23 01:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0006_student_password_alter_attendance_punch_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendance',
            name='subject',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.subject'),
        ),
        migrations.AddField(
            model_name='subject',
            name='total_lectures',
            field=models.IntegerField(default=0),
        ),
        migrations.CreateModel(
            name='SubjectAttendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True)),
                ('is_present', models.BooleanField(default=True)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.student')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.subject')),
            ],
            options={
                'ordering': ['-date'],
                'unique_together': {('student', 'subject', 'date')},
            },
        ),
    ]
