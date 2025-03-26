from django.db import migrations
from django.contrib.auth.hashers import make_password

def hash_existing_passwords(apps, schema_editor):
    Student = apps.get_model('app', 'Student')
    for student in Student.objects.all():
        if not student.password.startswith('pbkdf2_sha256$'):
            student.password = make_password(student.password)
            student.save()

def reverse_passwords(apps, schema_editor):
    Student = apps.get_model('app', 'Student')
    for student in Student.objects.all():
        student.password = '123'
        student.save()

class Migration(migrations.Migration):
    dependencies = [
        ('app', '0008_add_initial_subjects'),
    ]

    operations = [
        migrations.RunPython(hash_existing_passwords, reverse_passwords),
    ] 