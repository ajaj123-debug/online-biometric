from django.db import migrations

def add_missing_subjects(apps, schema_editor):
    Subject = apps.get_model('app', 'Subject')
    # First, delete all existing subjects
    Subject.objects.all().delete()
    
    # Add the new subjects
    subjects = [
        {'code': 'BHUM-005_AS', 'name': 'Humanities'},
        {'code': 'BELE-570_RG', 'name': 'Linear Integrated Circuit Analysis'},
        {'code': 'BPD-II', 'name': 'Professional Development II'},
        {'code': 'BECE-562_AG', 'name': 'Project Lab'},
        {'code': 'BECE-526_RL', 'name': 'Computer Network Lab'},
        {'code': 'BECE-524_KA', 'name': 'Control System'},
        {'code': 'BECE-555_AB', 'name': 'VHDL'},
        {'code': 'BECE-525_RL', 'name': 'Computer Network'},
        {'code': 'BECE-558_RG', 'name': 'Design Lab'}
    ]
    for subject in subjects:
        Subject.objects.create(**subject)

def remove_missing_subjects(apps, schema_editor):
    Subject = apps.get_model('app', 'Subject')
    Subject.objects.filter(code__in=[
        'BHUM-005_AS', 'BELE-570_RG', 'BPD-II', 'BECE-562_AG',
        'BECE-526_RL', 'BECE-524_KA', 'BECE-555_AB', 'BECE-525_RL',
        'BECE-558_RG'
    ]).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('app', '0013_student_roll_number'),
    ]

    operations = [
        migrations.RunPython(add_missing_subjects, remove_missing_subjects),
    ] 