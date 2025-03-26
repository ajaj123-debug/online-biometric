from django.contrib import admin
from django.contrib.admin import AdminSite
from .models import Student, Subject, SubjectAttendance, Attendance, SpecialWorkingDay

class ModernAdminSite(AdminSite):
    site_header = 'Biometric Attendance System'
    site_title = 'Biometric Attendance Portal'
    index_title = 'Welcome to the Biometric Attendance System'
    
    def each_context(self, request):
        context = super().each_context(request)
        context['custom_css'] = """
            :root {
                --primary: #1a73e8;
                --secondary: #4dabf7;
                --accent: #339af0;
                --primary-fg: #fff;
                --body-fg: #333;
                --body-bg: #f8f9fa;
                --header-color: #fff;
            }
            
            #header {
                background: var(--primary);
                color: var(--header-color);
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            #branding h1 {
                font-weight: 600;
            }
            
            .module h2, .module caption, .inline-group h2 {
                background: var(--primary);
                color: var(--header-color);
                padding: 12px 15px;
                border-radius: 4px;
            }
            
            div.breadcrumbs {
                background: var(--secondary);
                padding: 15px 20px;
                border: none;
                font-size: 14px;
                color: var(--header-color);
                border-radius: 4px;
                margin: 0 -20px 20px;
            }
            
            .button, input[type=submit], input[type=button], .submit-row input, a.button {
                background: var(--primary);
                padding: 10px 15px;
                border: none;
                border-radius: 4px;
                color: var(--header-color);
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .button:hover, input[type=submit]:hover, input[type=button]:hover {
                background: var(--accent);
            }
            
            .button.default, input[type=submit].default, .submit-row input.default {
                background: var(--primary);
            }
            
            .button.default:hover, input[type=submit].default:hover {
                background: var(--accent);
            }
            
            #content-related .module h2 {
                background: var(--primary);
                color: var(--header-color);
                padding: 12px 15px;
                border-radius: 4px 4px 0 0;
            }
            
            .module {
                background: white;
                border-radius: 4px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                border: 1px solid #eee;
                margin-bottom: 20px;
            }
            
            .submit-row {
                background: white;
                border: 1px solid #eee;
                border-radius: 4px;
                padding: 15px 20px;
            }
            
            a:link, a:visited {
                color: var(--primary);
                text-decoration: none;
            }
            
            a:hover {
                color: var(--accent);
            }
            
            #user-tools {
                font-size: 14px;
            }
            
            .object-tools a:link, .object-tools a:visited {
                background: var(--secondary);
                padding: 8px 12px;
                border-radius: 4px;
            }
            
            .object-tools a:hover {
                background: var(--accent);
            }
            
            thead th {
                background: #f8f9fa;
                color: var(--body-fg);
                font-weight: 600;
            }
            
            #content {
                padding: 20px;
            }
            
            .login #header {
                height: auto;
                padding: 15px;
            }
            
            .login #content {
                padding: 20px;
            }
            
            .login .form-row {
                padding: 10px 0;
            }
            
            .login .submit-row {
                padding: 15px 0;
                text-align: center;
            }
            
            .login .submit-row input {
                display: block;
                width: 100%;
                padding: 12px;
                font-size: 16px;
            }
        """
        return context

admin_site = ModernAdminSite(name='modern_admin')

# Register models with the custom admin site
admin_site.register(Student, StudentAdmin := type('StudentAdmin', (admin.ModelAdmin,), {
    'list_display': ('name', 'fingerprint_id', 'get_password'),
    'search_fields': ('name',),
    'get_password': lambda self, obj: '123',
}))

admin_site.register(Subject, SubjectAdmin := type('SubjectAdmin', (admin.ModelAdmin,), {
    'list_display': ('code', 'name', 'total_lectures'),
    'search_fields': ('code', 'name'),
}))

admin_site.register(SubjectAttendance, SubjectAttendanceAdmin := type('SubjectAttendanceAdmin', (admin.ModelAdmin,), {
    'list_display': ('student', 'subject', 'date', 'is_present'),
    'list_filter': ('subject', 'date', 'is_present'),
    'search_fields': ('student__name', 'subject__code'),
}))

admin_site.register(Attendance, AttendanceAdmin := type('AttendanceAdmin', (admin.ModelAdmin,), {
    'list_display': ('student', 'punch_time', 'punch_type', 'subject'),
    'list_filter': ('punch_type', 'subject'),
    'search_fields': ('student__name', 'subject__code'),
}))

admin_site.register(SpecialWorkingDay, SpecialWorkingDayAdmin := type('SpecialWorkingDayAdmin', (admin.ModelAdmin,), {
    'list_display': ('date', 'get_day_name', 'follow_timetable_of_display', 'is_active', 'description'),
    'list_filter': ('is_active', 'follow_timetable_of'),
    'search_fields': ('date', 'description'),
    'ordering': ('-date',),
    'get_day_name': lambda self, obj: obj.date.strftime("%A"),
    'follow_timetable_of_display': lambda self, obj: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][obj.follow_timetable_of],
}))
