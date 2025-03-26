from django.db import migrations, models

def create_initial_subjects(apps, schema_editor):
    Subject = apps.get_model('app', 'Subject')
    subjects = [
        {'code': 'BHUM-005_AS', 'name': 'Humanities'},
        {'code': 'BELE-570_RG', 'name': 'Linear Integrated Circuit Analysis (LICA)'},
        {'code': 'BPD-II', 'name': 'Professional Development II'},
        {'code': 'BECE-562_AG', 'name': 'Project Lab'},
        {'code': 'BECE-526_RL', 'name': 'Computer Network Lab'}
    ]
    for subject in subjects:
        Subject.objects.create(**subject)

def remove_initial_subjects(apps, schema_editor):
    Subject = apps.get_model('app', 'Subject')
    Subject.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('app', '0003_attendance'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=20, unique=True)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ['code'],
            },
        ),
        migrations.RunPython(create_initial_subjects, remove_initial_subjects),
    ] 