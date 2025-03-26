from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Student(models.Model):
    name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=20, unique=True, null=True, blank=True)  # Making it nullable initially
    fingerprint_id = models.IntegerField(null=True, blank=True, unique=True)
    password = models.CharField(max_length=128, default='123')  # Default password is '123'
    
    def __str__(self):
        return f"{self.name} ({self.roll_number})" if self.roll_number else self.name
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    def save(self, *args, **kwargs):
        # Hash the password if it's not already hashed
        if not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

class SpecialWorkingDay(models.Model):
    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
    ]
    
    date = models.DateField(unique=True)
    follow_timetable_of = models.IntegerField(choices=WEEKDAY_CHOICES)
    is_active = models.BooleanField(default=True)
    description = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return f"{self.date} (Following {self.get_follow_timetable_of_display()})"
    
    class Meta:
        ordering = ['-date']

class Subject(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    total_lectures = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        ordering = ['code']

class SubjectAttendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    date = models.DateField()
    is_present = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['student', 'subject', 'date']
        ordering = ['-date']
    
    def __str__(self):
        status = "Present" if self.is_present else "Absent"
        return f"{self.student.name} - {self.subject.code} - {status} on {self.date}"

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    punch_time = models.DateTimeField(auto_now_add=True)
    punch_type = models.CharField(max_length=3, choices=[('IN', 'In'), ('OUT', 'Out')])
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return f"{self.student.name} - {self.punch_type} at {self.punch_time}"

    class Meta:
        ordering = ['-punch_time']
