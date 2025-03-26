from django.urls import path
from app import views
from app.admin import admin_site

urlpatterns = [
    path('admin/', admin_site.urls),
    path('', views.index, name='index'),
    path('students/', views.student_list, name='student_list'),
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('api/punch/', views.punch_attendance, name='punch_attendance'),
    path('api/students/', views.student_json, name='student_json'),
    path('api/students/add/', views.add_student, name='add_student'),
    path('api/students/<int:student_id>/delete/', views.delete_student, name='delete_student'),
    path('api/students/<int:student_id>/enroll/', views.enroll_fingerprint, name='enroll_fingerprint'),
    path('api/students/<int:student_id>/start_enrollment/', views.start_enrollment, name='start_enrollment'),
    path('api/students/<int:student_id>/check_enrollment/', views.check_enrollment, name='check_enrollment'),
    path('api/check_enrollment_command/', views.check_enrollment_command, name='check_enrollment_command'),
    path('api/check_delete_command/', views.check_delete_command, name='check_delete_command'),
    path('api/check_special_working_day/', views.check_special_working_day, name='check_special_working_day'),
    # Special working days management
    path('special-days/', views.manage_special_days, name='manage_special_days'),
    path('special-days/<int:special_day_id>/delete/', views.delete_special_day, name='delete_special_day'),
    # Student login and attendance URLs
    path('student/login/', views.student_login, name='student_login'),
    path('student/logout/', views.student_logout, name='student_logout'),
    path('student/attendance/', views.student_attendance, name='student_attendance'),
]