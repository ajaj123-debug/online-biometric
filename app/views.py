from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Student, Attendance, Subject, SubjectAttendance, SpecialWorkingDay
import json
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from django.contrib import messages
import math
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required

# Global variable to store the current enrollment command
current_enrollment_command = {"student_id": -1}

def index(request):
    """Landing page view with system status"""
    total_students = Student.objects.count()
    today = datetime.now().date()
    today_attendance = Attendance.objects.filter(punch_time__date=today).count()
    enrolled_fingerprints = Student.objects.filter(fingerprint_id__isnull=False).count()
    
    return render(request, 'index.html', {
        'total_students': total_students,
        'today_attendance': today_attendance,
        'enrolled_fingerprints': enrolled_fingerprints
    })

@staff_member_required
def student_list(request):
    students = Student.objects.all()
    return render(request, 'students.html', {'students': students})

def attendance_list(request):
    # Get attendance records for the last 7 days
    start_date = datetime.now() - timedelta(days=7)
    attendance_records = Attendance.objects.filter(punch_time__gte=start_date).order_by('-punch_time')
    
    # Group attendance records by date
    attendance_by_date = {}
    for record in attendance_records:
        date = record.punch_time.date()
        if date not in attendance_by_date:
            attendance_by_date[date] = []
        attendance_by_date[date].append(record)
    
    return render(request, 'attendance.html', {
        'attendance_by_date': attendance_by_date,
        'start_date': start_date.date()
    })

@csrf_exempt
def punch_attendance(request):
    """
    Handle attendance punching from ESP32
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            fingerprint_id = data.get("fingerprint_id")
            subject_code = data.get("subject_code")  # New parameter for subject
            
            if fingerprint_id is None:
                return JsonResponse({
                    "status": "error",
                    "message": "No fingerprint ID provided"
                }, status=400)
            
            # Find student with this fingerprint
            student = Student.objects.filter(fingerprint_id=fingerprint_id).first()
            if not student:
                return JsonResponse({
                    "status": "error",
                    "message": "No student found with this fingerprint"
                }, status=400)
            
            # Get subject if code provided
            subject = None
            if subject_code:
                subject = Subject.objects.filter(code=subject_code).first()
                if not subject:
                    return JsonResponse({
                        "status": "error",
                        "message": f"Invalid subject code: {subject_code}"
                    }, status=400)
            
            # Check last punch type
            last_punch = Attendance.objects.filter(student=student).order_by('-punch_time').first()
            punch_type = 'OUT' if last_punch and last_punch.punch_type == 'IN' else 'IN'
            
            # Create attendance record
            attendance = Attendance.objects.create(
                student=student,
                punch_type=punch_type,
                subject=subject
            )
            
            # If this is an IN punch and subject is provided, create subject attendance
            if punch_type == 'IN' and subject:
                # Increment total lectures for the subject
                subject.total_lectures += 1
                subject.save()
                
                # Create subject attendance record
                SubjectAttendance.objects.create(
                    student=student,
                    subject=subject,
                    date=attendance.punch_time.date()
                )
                
                # Calculate current attendance percentage
                attended_lectures = SubjectAttendance.objects.filter(
                    student=student,
                    subject=subject,
                    is_present=True
                ).count()
                
                total_lectures = subject.total_lectures
                percentage = (attended_lectures / total_lectures) * 100 if total_lectures > 0 else 0
            
            return JsonResponse({
                "status": "success",
                "message": f"Attendance recorded for {student.name} ({punch_type})",
                "student_name": student.name,
                "punch_type": punch_type,
                "punch_time": attendance.punch_time.strftime("%Y-%m-%d %H:%M:%S"),
                "subject": subject.code if subject else None,
                "attendance_percentage": round(percentage, 2) if punch_type == 'IN' and subject else None
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                "status": "error",
                "message": "Invalid JSON data"
            }, status=400)
    
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

@csrf_exempt
def add_student(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            name = data.get("name")
            roll_number = data.get("roll_number")
            
            if not name or not roll_number:
                return JsonResponse({
                    "status": "error", 
                    "message": "Both name and roll number are required"
                }, status=400)
            
            # Check if roll number already exists
            if Student.objects.filter(roll_number=roll_number).exists():
                return JsonResponse({
                    "status": "error",
                    "message": "Roll number already exists"
                }, status=400)
            
            student = Student.objects.create(
                name=name,
                roll_number=roll_number
            )
            return JsonResponse({"status": "success", "student_id": student.id})
            
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

@csrf_exempt
def enroll_fingerprint(request, student_id):
    """
    This function waits for the ESP32 to send a fingerprint ID after scanning.
    """
    if request.method == "POST":
        student = get_object_or_404(Student, id=student_id)
        
        try:
            data = json.loads(request.body)
            fingerprint_id = data.get("fingerprint_id")
            is_duplicate = data.get("is_duplicate", False)
            existing_id = data.get("existing_id")
            
            if is_duplicate:
                existing_student = Student.objects.filter(fingerprint_id=existing_id).first()
                if existing_student:
                    return JsonResponse({
                        "status": "error", 
                        "message": f"This fingerprint is already enrolled for student: {existing_student.name} (ID: {existing_id})"
                    }, status=400)
                else:
                    return JsonResponse({
                        "status": "error", 
                        "message": f"This fingerprint is already enrolled (ID: {existing_id})"
                    }, status=400)
            
            if fingerprint_id is not None and fingerprint_id != -2:  # Ignore special duplicate code
                # Check if this fingerprint is already enrolled for another student
                if Student.objects.filter(fingerprint_id=fingerprint_id).exclude(id=student_id).exists():
                    existing_student = Student.objects.filter(fingerprint_id=fingerprint_id).first()
                    return JsonResponse({
                        "status": "error", 
                        "message": f"This fingerprint is already enrolled for student: {existing_student.name} (ID: {fingerprint_id})"
                    }, status=400)
                
                student.fingerprint_id = fingerprint_id
                student.save()
                return JsonResponse({
                    "status": "success", 
                    "fingerprint_id": fingerprint_id,
                    "message": "Fingerprint enrolled successfully"
                })
            else:
                return JsonResponse({
                    "status": "error", 
                    "message": "No fingerprint ID provided"
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                "status": "error", 
                "message": "Invalid JSON data"
            }, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

def student_json(request):
    students = list(Student.objects.values("id", "name", "fingerprint_id"))
    return JsonResponse(students, safe=False)

@csrf_exempt
def delete_student(request, student_id):
    if request.method == "POST":
        try:
            student = get_object_or_404(Student, id=student_id)
            fingerprint_id = student.fingerprint_id
            student.delete()
            
            # If student had a fingerprint, send command to ESP32 to delete it
            if fingerprint_id is not None:
                # Send HTTP request to ESP32 to delete the fingerprint
                try:
                    response = request.get(f"http://192.168.48.104:8000/api/check_delete_command/?fingerprint_id={fingerprint_id}")
                    if response.status_code != 200:
                        print(f"Failed to delete fingerprint {fingerprint_id} from ESP32")
                except Exception as e:
                    print(f"Error deleting fingerprint from ESP32: {str(e)}")
            
            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

@csrf_exempt
def start_enrollment(request, student_id):
    """
    Start the fingerprint enrollment process for a student
    """
    if request.method == "POST":
        student = get_object_or_404(Student, id=student_id)
        current_enrollment_command["student_id"] = student_id
        return JsonResponse({
            "status": "success",
            "message": "Enrollment process started"
        })
    
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

@csrf_exempt
def check_enrollment(request, student_id):
    """
    Check the status of fingerprint enrollment for a student
    """
    if request.method == "GET":
        student = get_object_or_404(Student, id=student_id)
        
        # Check if this student's fingerprint is already enrolled for another student
        if Student.objects.filter(fingerprint_id=student.fingerprint_id).exclude(id=student_id).exists():
            return JsonResponse({
                "status": "error",
                "message": "This fingerprint is already enrolled for another student"
            })
        
        if student.fingerprint_id:
            return JsonResponse({
                "status": "success",
                "message": "Fingerprint enrolled"
            })
        else:
            return JsonResponse({
                "status": "pending",
                "message": "Waiting for fingerprint"
            })
    
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

@csrf_exempt
def check_enrollment_command(request):
    """
    Endpoint for ESP32 to check for enrollment commands
    """
    if request.method == "GET":
        command = current_enrollment_command.copy()
        # Reset the command after sending
        current_enrollment_command["student_id"] = -1
        return JsonResponse(command)
    
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

@csrf_exempt
def check_delete_command(request):
    """
    Endpoint for ESP32 to check for fingerprint deletion commands
    """
    if request.method == "GET":
        # Get the fingerprint ID from the request
        fingerprint_id = request.GET.get('fingerprint_id')
        if fingerprint_id:
            return JsonResponse({
                'fingerprint_id': int(fingerprint_id)
            })
        return JsonResponse({
            'fingerprint_id': -1
        })
    
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

def student_login(request):
    if request.method == "POST":
        name = request.POST.get("name")
        password = request.POST.get("password")
        
        try:
            student = Student.objects.get(name=name)
            if student.check_password(password):
                request.session['student_id'] = student.id
                return redirect('student_attendance')
            else:
                return render(request, 'student_login.html', {'error': 'Invalid password'})
        except Student.DoesNotExist:
            return render(request, 'student_login.html', {'error': 'Student not found'})
    
    return render(request, 'student_login.html')

def student_logout(request):
    if 'student_id' in request.session:
        del request.session['student_id']
    return redirect('student_login')

def student_attendance(request):
    if 'student_id' not in request.session:
        return redirect('student_login')
    
    student = get_object_or_404(Student, id=request.session['student_id'])
    
    # Get all subjects
    subjects = Subject.objects.all()
    
    # Calculate attendance percentage and required lectures for each subject
    subject_attendance = []
    for subject in subjects:
        # Get total attended lectures
        attended_lectures = SubjectAttendance.objects.filter(
            student=student,
            subject=subject,
            is_present=True
        ).count()
        
        # Calculate percentage
        total_lectures = max(subject.total_lectures, 1)  # Ensure we don't divide by zero
        percentage = (attended_lectures / total_lectures) * 100
            
        # Calculate lectures needed for 90% attendance
        if percentage < 90:
            current_total = total_lectures
            current_attended = attended_lectures
            while (current_attended / current_total) * 100 < 90:
                current_attended += 1
                current_total += 1
            lectures_needed = current_attended - attended_lectures
        else:
            lectures_needed = 0
            
        subject_attendance.append({
            'code': subject.code,
            'name': subject.name,
            'total_lectures': subject.total_lectures,
            'attended_lectures': attended_lectures,
            'percentage': round(percentage, 2) if subject.total_lectures > 0 else 0,
            'lectures_needed': lectures_needed
        })
    
    # Get recent attendance records
    attendance_records = Attendance.objects.filter(
        student=student
    ).select_related('subject').order_by('-punch_time')[:10]
    
    return render(request, 'student_attendance.html', {
        'student': student,
        'subject_attendance': subject_attendance,
        'attendance_records': attendance_records,
    })

def get_attendance_stats(request):
    """
    Get attendance statistics for a student
    """
    student_id = request.GET.get('student_id')
    if not student_id:
        return JsonResponse({
            "status": "error",
            "message": "Student ID is required"
        }, status=400)
    
    try:
        student = Student.objects.get(id=student_id)
        stats = []
        
        # Get all subjects
        subjects = Subject.objects.all()
        
        for subject in subjects:
            # Get total lectures conducted for this subject
            total_lectures = subject.total_lectures
            
            # Get number of lectures attended by this student
            attended_lectures = SubjectAttendance.objects.filter(
                student=student,
                subject=subject,
                is_present=True
            ).count()
            
            # Calculate percentage
            percentage = (attended_lectures / total_lectures * 100) if total_lectures > 0 else 0
            
            # Calculate lectures needed for 90% attendance
            lectures_needed = 0
            if percentage < 90 and total_lectures > 0:
                # Formula: (90 * total_lectures - 100 * attended_lectures) / 10
                lectures_needed = math.ceil((90 * total_lectures - 100 * attended_lectures) / 10)
            
            stats.append({
                "subject_code": subject.code,
                "subject_name": subject.name,
                "total_lectures": total_lectures,
                "attended_lectures": attended_lectures,
                "percentage": round(percentage, 2),
                "lectures_needed": lectures_needed
            })
        
        return JsonResponse({
            "status": "success",
            "student_name": student.name,
            "stats": stats
        })
        
    except Student.DoesNotExist:
        return JsonResponse({
            "status": "error",
            "message": "Student not found"
        }, status=404)
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)

def check_special_working_day(request):
    # Get today's date in the local timezone
    today = timezone.localtime(timezone.now()).date()
    try:
        special_day = SpecialWorkingDay.objects.get(date=today, is_active=True)
        return JsonResponse({
            'is_special_day': True,
            'follow_day': special_day.follow_timetable_of,
            'description': special_day.description
        })
    except SpecialWorkingDay.DoesNotExist:
        return JsonResponse({
            'is_special_day': False,
            'follow_day': -1,
            'description': ''
        })

@staff_member_required
def manage_special_days(request):
    if request.method == "POST":
        date = request.POST.get('date')
        follow_day = request.POST.get('follow_day')
        description = request.POST.get('description')
        is_active = request.POST.get('is_active') == 'on'

        try:
            special_day, created = SpecialWorkingDay.objects.update_or_create(
                date=date,
                defaults={
                    'follow_timetable_of': follow_day,
                    'description': description,
                    'is_active': is_active
                }
            )
            messages.success(request, 'Special working day saved successfully!')
        except Exception as e:
            messages.error(request, f'Error saving special working day: {str(e)}')
        
        return redirect('manage_special_days')

    # Get all special days and upcoming ones
    all_special_days = SpecialWorkingDay.objects.all().order_by('-date')
    upcoming_special_days = SpecialWorkingDay.objects.filter(
        date__gte=timezone.now().date(),
        is_active=True
    ).order_by('date')

    return render(request, 'manage_special_days.html', {
        'all_special_days': all_special_days,
        'upcoming_special_days': upcoming_special_days,
        'weekdays': SpecialWorkingDay.WEEKDAY_CHOICES
    })

@staff_member_required
@csrf_exempt
def delete_special_day(request, special_day_id):
    if request.method == "POST":
        try:
            special_day = get_object_or_404(SpecialWorkingDay, id=special_day_id)
            special_day.delete()
            messages.success(request, 'Special working day deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting special working day: {str(e)}')
    
    return redirect('manage_special_days')