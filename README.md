# Online Biometric Attendance System Using R307s and Wroom Esp32 Dev

This project is a Biometric Attendance System built using Django. It allows students to punch their attendance using fingerprint scanners and provides various functionalities for managing students, subjects, and attendance records.

## Features

- **Student Management**: Add, delete, and list students.
- **Attendance Management**: Punch attendance using fingerprint scanners, view attendance records, and calculate attendance percentages.
- **Subject Management**: Manage subjects and their attendance records.
- **Special Working Days**: Manage special working days and their schedules.
- **Student Login**: Students can log in to view their attendance records and statistics.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/biometric-attendance-system.git
    cd biometric-attendance-system
    ```

2. Create a virtual environment and activate it:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Apply migrations:
    ```bash
    python manage.py migrate
    ```

5. Create a superuser:
    ```bash
    python manage.py createsuperuser
    ```

6. Run the development server:
    ```bash
    python manage.py runserver
    ```

7. Access the application at `http://127.0.0.1:8000/`.

## Usage

### Admin Panel

- Access the admin panel at `http://127.0.0.1:8000/admin/` using the superuser credentials.
- Manage students, subjects, attendance records, and special working days.

### Student Attendance

- Students can log in at `http://127.0.0.1:8000/student_login/` to view their attendance records and statistics.

### API Endpoints

- **Punch Attendance**: `POST /punch_attendance/`
- **Add Student**: `POST /add_student/`
- **Enroll Fingerprint**: `POST /enroll_fingerprint/<student_id>/`
- **Delete Student**: `POST /delete_student/<student_id>/`
- **Start Enrollment**: `POST /start_enrollment/<student_id>/`
- **Check Enrollment**: `GET /check_enrollment/<student_id>/`
- **Check Enrollment Command**: `GET /check_enrollment_command/`
- **Check Delete Command**: `GET /check_delete_command/`
- **Get Attendance Stats**: `GET /get_attendance_stats/`
- **Check Special Working Day**: `GET /check_special_working_day/`
- **Manage Special Days**: `POST /manage_special_days/`
- **Delete Special Day**: `POST /delete_special_day/<special_day_id>/`

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
