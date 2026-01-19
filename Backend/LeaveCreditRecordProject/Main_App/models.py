from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password

class HRUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    full_name = models.CharField(max_length=255)
    is_hr = models.BooleanField(default=True)

    gender = models.CharField(max_length=20, null=True, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)

    photo = models.ImageField(
        upload_to='hr_photos/',
        null=True,
        blank=True,
        default='assets/media/examplePIC.jpg'
    )

    @property
    def position(self):
        return "Human Resource"

    def __str__(self):
        return f"{self.full_name} ({self.user.username})"

class AccessKey(models.Model):
    key_hash = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)


class Department(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Position(models.Model):
    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title

class Employee(models.Model):
    GENDER_CHOICES = [('male', 'Male'), ('female', 'Female'), ('other', 'Other')]
    employee_id = models.CharField(max_length=20, unique=True, editable=False)
    full_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    age = models.IntegerField(validators=[MinValueValidator(18), MaxValueValidator(100)])
    height = models.DecimalField(max_digits=5, decimal_places=2, help_text="Height in cm")
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text="Weight in kg")
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='employees')
    position = models.ForeignKey(Position, on_delete=models.PROTECT, related_name='employees')
    photo = models.ImageField(upload_to='employee_photos/', blank=True, null=True)
    motto_in_life = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_created']
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'

    def save(self, *args, **kwargs):
        if not self.employee_id:
            year = timezone.now().year
            last_employee = Employee.objects.filter(employee_id__startswith=f'OC-{year}').order_by('employee_id').last()
            if last_employee:
                last_number = int(last_employee.employee_id.split('-')[1][4:])
                new_number = last_number + 1
            else:
                new_number = 1
            self.employee_id = f'OC-{year}{new_number:04d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee_id} - {self.full_name}"

class EmployeeLeaveBalance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_balances')
    year = models.PositiveIntegerField()
    remaining_days = models.PositiveIntegerField(default=15)  # Every employee starts with 15 days

    class Meta:
        unique_together = ('employee', 'year')

    def __str__(self):
        return f"{self.employee.full_name} - {self.year}: {self.remaining_days} days left"

    def deduct_days(self, days):
        if days > self.remaining_days:
            raise ValueError("Cannot deduct more days than remaining")
        self.remaining_days -= days
        self.save()

class LeaveApplication(models.Model):
    LEAVE_TYPES = [
        ('vacation', 'Vacation Leave'),
        ('sick', 'Sick Leave'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
        ('emergency', 'Emergency Leave'),
    ]
    LOCATION_CHOICES = [('philippines', 'Within the Philippines'), ('abroad', 'Abroad')]
    SICK_LOCATION_CHOICES = [('hospital', 'In Hospital'), ('home', 'At Home')]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_applications')
    leave_type = models.CharField(max_length=50, choices=LEAVE_TYPES)
    vacation_location = models.CharField(max_length=50, choices=LOCATION_CHOICES, blank=True, null=True)
    sick_location = models.CharField(max_length=50, choices=SICK_LOCATION_CHOICES, blank=True, null=True)
    number_of_days = models.PositiveIntegerField(validators=[MinValueValidator(1)], default=1)
    reason = models.TextField(blank=True) 
    date_filed = models.DateField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending'
    )

    class Meta:
        ordering = ['-date_filed']

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type} ({self.date_filed})"

class Dean(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dean_profile')
    
    full_name = models.CharField(max_length=255)
    is_dean = models.BooleanField(default=True)
    
    department = models.ForeignKey(
        'Department', 
        on_delete=models.PROTECT, 
        related_name='dean',
        help_text="Department this dean manages"
    )
    
    gender = models.CharField(max_length=20, null=True, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    
    photo = models.ImageField(
        upload_to='dean_photos/',
        null=True,
        blank=True,
        default='static/assets/media/examplePIC.jpg'
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def position(self):
        return "Dean"

    class Meta:
        ordering = ['full_name']
        verbose_name = 'Dean'
        verbose_name_plural = 'Deans'

    def __str__(self):
        return f"{self.full_name} - Dean of {self.department.name}"


class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('dean_approved', 'Dean Approved'),
        ('dean_denied', 'Dean Denied'),
        ('approved', 'HR Approved'),
        ('denied', 'HR Denied')
    ]

    application = models.OneToOneField(
        'LeaveApplication',
        on_delete=models.CASCADE,
        related_name='leave_request'
    )
    
    dean_reviewer = models.ForeignKey(
        'Dean', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='dean_reviews'
    )
    dean_reviewed_at = models.DateTimeField(null=True, blank=True)
    dean_comments = models.TextField(blank=True)
    
    hr_reviewer = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='hr_reviews'
    )
    hr_reviewed_at = models.DateTimeField(null=True, blank=True)
    hr_comments = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_archived = models.BooleanField(
        default=False,
        help_text="True if auto-archived, False if manually archived"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Leave Request'
        verbose_name_plural = 'Leave Requests'

    def _create_report(self, reviewer_type, reviewer, comments=None):
        application = self.application

        report, created = LeaveReport.objects.get_or_create(
            leave_request=self,
            defaults={
                'employee': application.employee,
                'leave_type': application.leave_type,
                'number_of_days': application.number_of_days,
                'location': application.vacation_location or application.sick_location or 'N/A',
                'date_filed': application.date_filed,
            }
        )

        if reviewer_type == 'dean':
            report.dean_reviewer = reviewer
            report.dean_status = 'denied' if self.status == 'dean_denied' else 'approved'
            report.dean_reviewed_at = self.dean_reviewed_at
            report.dean_comments = comments or ''

        elif reviewer_type == 'hr':
            report.hr_reviewer = reviewer
            report.hr_status = 'denied' if self.status == 'denied' else 'approved'
            report.hr_reviewed_at = self.hr_reviewed_at
            report.hr_comments = comments or ''

        report.save()
        return report


    def dean_approve(self, dean):
        self.status = 'dean_approved'
        self.dean_reviewer = dean
        self.dean_reviewed_at = timezone.now()
        self.save()

        self.application.status = 'pending'
        self.application.save()

        self._create_report('dean', dean, self.dean_comments)


    def dean_deny(self, dean, comments=''):
        self.status = 'dean_denied'
        self.dean_reviewer = dean
        self.dean_reviewed_at = timezone.now()
        self.dean_comments = comments
        self.save()

        self.application.status = 'rejected'
        self.application.save()

        self._create_report('dean', dean, comments)


    def hr_approve(self, hr_user):
        if self.status != 'dean_approved':
            raise ValueError("Leave request must be dean-approved first")

        self.status = 'approved'
        self.hr_reviewer = hr_user
        self.hr_reviewed_at = timezone.now()
        self.save()

        self.application.status = 'approved'
        self.application.save()

        year = timezone.now().year
        balance, created = EmployeeLeaveBalance.objects.get_or_create(
            employee=self.application.employee,
            year=year
        )
        balance.deduct_days(self.application.number_of_days)

        self._create_report('hr', hr_user, self.hr_comments)


    def hr_deny(self, hr_user, comments=''):
        if self.status != 'dean_approved':
            raise ValueError("Leave request must be dean-approved first")

        self.status = 'denied'
        self.hr_reviewer = hr_user
        self.hr_reviewed_at = timezone.now()
        self.hr_comments = comments
        self.save()

        self.application.status = 'rejected'
        self.application.save()

        self._create_report('hr', hr_user, comments)


    @property
    def is_pending_dean_approval(self):
        return self.status == 'pending'
    
    @property
    def is_pending_hr_approval(self):
        return self.status == 'dean_approved'

    def __str__(self):
        return f"{self.application.employee.full_name} - {self.status}"

class LeaveReport(models.Model):
    DEAN_STATUS_CHOICES = [
        ('pending', 'Pending Dean Review'),
        ('approved', 'Dean Approved'),
        ('denied', 'Dean Denied'),
    ]
    HR_STATUS_CHOICES = [
        ('pending', 'Pending HR Review'),
        ('approved', 'HR Approved'),
        ('denied', 'HR Denied'),
    ]

    leave_request = models.OneToOneField(
        'LeaveRequest', on_delete=models.CASCADE, related_name='report'
    )
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_reports')
    leave_type = models.CharField(max_length=50)
    number_of_days = models.PositiveIntegerField()
    location = models.CharField(max_length=50)
    date_filed = models.DateField()

    dean_status = models.CharField(max_length=20, choices=DEAN_STATUS_CHOICES, default='pending')
    hr_status = models.CharField(max_length=20, choices=HR_STATUS_CHOICES, default='pending')

    dean_reviewer = models.ForeignKey(
        'Dean', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_reports'
    )
    hr_reviewer = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='hr_reviewed_reports'
    )

    dean_reviewed_at = models.DateTimeField(null=True, blank=True)
    hr_reviewed_at = models.DateTimeField(null=True, blank=True)

    dean_comments = models.TextField(blank=True)
    hr_comments = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Leave Report'
        verbose_name_plural = 'Leave Reports'

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type} Report"

    @classmethod
    def create_or_update_from_leave_request(cls, leave_request):
        report, created = cls.objects.get_or_create(
            leave_request=leave_request,
            defaults={
                'employee': leave_request.application.employee,
                'leave_type': leave_request.application.leave_type,
                'number_of_days': leave_request.application.number_of_days,
                'location': leave_request.application.vacation_location or leave_request.application.sick_location or 'N/A',
                'date_filed': leave_request.application.date_filed,
            }
        )

        if leave_request.dean_reviewer:
            report.dean_reviewer = leave_request.dean_reviewer
            report.dean_status = 'approved' if leave_request.status != 'dean_denied' else 'denied'
            report.dean_reviewed_at = leave_request.dean_reviewed_at
            report.dean_comments = leave_request.dean_comments or ''

        if leave_request.hr_reviewer:
            report.hr_reviewer = leave_request.hr_reviewer
            report.hr_status = 'approved' if leave_request.status == 'approved' else 'denied'
            report.hr_reviewed_at = leave_request.hr_reviewed_at
            report.hr_comments = leave_request.hr_comments or ''

        report.save()
        return report

class LeaveRequestArchive(models.Model):
    STATUS_CHOICES = [
        ('approved', 'Approved by Dean and HR'),
        ('denied', 'Approved by Dean, Denied by HR')
    ]
    
    LEAVE_TYPES = [
        ('vacation', 'Vacation Leave'),
        ('sick', 'Sick Leave'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
        ('emergency', 'Emergency Leave'),
    ]
    
    original_leave_request_id = models.IntegerField(help_text="Original LeaveRequest ID")
    original_leave_application_id = models.IntegerField(help_text="Original LeaveApplication ID")
    
    employee_id = models.CharField(max_length=20, help_text="Employee ID from original employee")
    employee_name = models.CharField(max_length=200)
    employee_department = models.CharField(max_length=100)
    employee_position = models.CharField(max_length=100)
    
    leave_type = models.CharField(max_length=50, choices=LEAVE_TYPES)
    number_of_days = models.PositiveIntegerField()
    vacation_location = models.CharField(max_length=50, blank=True, null=True)
    sick_location = models.CharField(max_length=50, blank=True, null=True)
    reason = models.TextField(blank=True)
    date_filed = models.DateField()
    
    dean_name = models.CharField(max_length=255)
    dean_department = models.CharField(max_length=100)
    dean_reviewed_at = models.DateTimeField()
    dean_comments = models.TextField(blank=True)

    hr_reviewer_username = models.CharField(max_length=150)
    hr_reviewer_name = models.CharField(max_length=255)
    hr_reviewed_at = models.DateTimeField()
    hr_comments = models.TextField(blank=True)
    
    final_status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    leave_balance_before = models.PositiveIntegerField(help_text="Days remaining before this request")
    leave_balance_after = models.PositiveIntegerField(null=True, blank=True, help_text="Days remaining after (only if approved)")
    leave_balance_year = models.PositiveIntegerField()

    archived_at = models.DateTimeField(auto_now_add=True)
    archived_by_system = models.BooleanField(default=True, help_text="True if auto-archived, False if manually archived")
    
    class Meta:
        ordering = ['-archived_at']
        verbose_name = 'Leave Request Archive'
        verbose_name_plural = 'Leave Request Archives'
        indexes = [
            models.Index(fields=['employee_id', '-archived_at']),
            models.Index(fields=['final_status', '-archived_at']),
            models.Index(fields=['-date_filed']),
        ]
    
    def __str__(self):
        return f"{self.employee_name} ({self.employee_id}) - {self.leave_type} - {self.final_status}"
    
    @classmethod
    def archive_leave_request(cls, leave_request):
        if leave_request.status not in ['approved', 'denied']:
            raise ValueError("Can only archive leave requests with final status (approved/denied)")
        
        if not leave_request.dean_reviewer or not leave_request.hr_reviewer:
            raise ValueError("Leave request must be reviewed by both dean and HR")
        
        application = leave_request.application
        employee = application.employee
        
        year = timezone.now().year
        try:
            balance = EmployeeLeaveBalance.objects.get(employee=employee, year=year)
            balance_before = balance.remaining_days
            if leave_request.status == 'approved':
                balance_after = balance.remaining_days 
            else:
                balance_after = balance.remaining_days 
        except EmployeeLeaveBalance.DoesNotExist:
            balance_before = 0
            balance_after = 0

        final_status = 'approved' if leave_request.status == 'approved' else 'denied'
        
        archive = cls.objects.create(
            original_leave_request_id=leave_request.id,
            original_leave_application_id=application.id,
            
            employee_id=employee.employee_id,
            employee_name=employee.full_name,
            employee_department=employee.department.name,
            employee_position=employee.position.title,
            
            leave_type=application.leave_type,
            number_of_days=application.number_of_days,
            vacation_location=application.vacation_location,
            sick_location=application.sick_location,
            reason=application.reason,
            date_filed=application.date_filed,
            
            dean_name=leave_request.dean_reviewer.full_name,
            dean_department=leave_request.dean_reviewer.department.name,
            dean_reviewed_at=leave_request.dean_reviewed_at,
            dean_comments=leave_request.dean_comments,
            
            hr_reviewer_username=leave_request.hr_reviewer.username,
            hr_reviewer_name=leave_request.hr_reviewer.get_full_name() or leave_request.hr_reviewer.username,
            hr_reviewed_at=leave_request.hr_reviewed_at,
            hr_comments=leave_request.hr_comments,
            
            final_status=final_status,
            leave_balance_before=balance_before + application.number_of_days if final_status == 'approved' else balance_before,
            leave_balance_after=balance_after if final_status == 'approved' else None,
            leave_balance_year=year,
        )
        
        return archive
    
    def get_summary(self):
        return {
            'employee': f"{self.employee_name} ({self.employee_id})",
            'department': self.employee_department,
            'position': self.employee_position,
            'leave_type': self.get_leave_type_display(),
            'days_requested': self.number_of_days,
            'date_filed': self.date_filed,
            'dean_decision': 'Approved',
            'dean_reviewer': f"{self.dean_name} (Dean of {self.dean_department})",
            'dean_date': self.dean_reviewed_at,
            'hr_decision': 'Approved' if self.final_status == 'approved' else 'Denied',
            'hr_reviewer': self.hr_reviewer_name,
            'hr_date': self.hr_reviewed_at,
            'final_outcome': self.get_final_status_display(),
            'archived_on': self.archived_at,
        }