from django.db import migrations

def create_initial_subjects(apps, schema_editor):
    Subject = apps.get_model('app', 'Subject')
    subjects = [
        {'code': 'BHUM-005_AS', 'name': 'Humanities'},
        {'code': 'BELE-570_RG', 'name': 'Linear Integrated Circuit Analysis (LICA)'},
        {'code': 'BPD-II', 'name': 'Professional Development II'},
        {'code': 'BECE-562_AG', 'name': 'Project Lab'},
        {'code': 'BECE-526_RL', 'name': 'Computer Network Lab'},
        {'code': 'BECE-524_KA', 'name': 'Control System'},
        {'code': 'BECE-555_AB', 'name': 'VHDL'},
        {'code': 'BECE-525_RL', 'name': 'Computer Network'},
        {'code': 'BECE-558_RG', 'name': 'Design Lab'}
    ]
    for subject in subjects:
        Subject.objects.get_or_create(code=subject['code'], defaults=subject)

def remove_initial_subjects(apps, schema_editor):
    Subject = apps.get_model('app', 'Subject')
    Subject.objects.filter(code__in=[
        'BHUM-005_AS', 'BELE-570_RG', 'BPD-II', 'BECE-562_AG',
        'BECE-526_RL', 'BECE-524_KA', 'BECE-555_AB', 'BECE-525_RL',
        'BECE-558_RG'
    ]).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('app', '0007_attendance_subject_subject_total_lectures_and_more'),
    ]

    operations = [
        migrations.RunPython(create_initial_subjects, remove_initial_subjects),
    ] 