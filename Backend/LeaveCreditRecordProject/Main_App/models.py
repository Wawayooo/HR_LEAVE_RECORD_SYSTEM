from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth.models import User

# ----------------- HASHED KEYS -----------------

from django.db import models
from django.contrib.auth.hashers import make_password, check_password

from django.contrib.auth.hashers import make_password, check_password
from django.db import models

from django.contrib.auth.hashers import make_password, check_password
from django.db import models

from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class HRUser(models.Model):
    # Link to Django's built-in User
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    # HR-specific fields
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
    # Store only one key (or multiple if you want rotation)
    key_hash = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)


# ----------------- Department -----------------
class Department(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


# ----------------- Position -----------------
class Position(models.Model):
    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title

# ----------------- Employee -----------------
class Employee(models.Model):
    GENDER_CHOICES = [('male', 'Male'), ('female', 'Female'), ('other', 'Other')]

    employee_id = models.CharField(max_length=20, unique=True, editable=False)
    full_name = models.CharField(max_length=200)
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
    
# models.py

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

# ----------------- Leave Application -----------------
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
    reason = models.TextField(blank=True)  # optional field for employee to state reason
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

# ----------------- Leave Request (Approval) -----------------
class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied')
    ]

    application = models.OneToOneField(
        LeaveApplication,
        on_delete=models.CASCADE,
        related_name='leave_request'
    )
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comments = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Leave Request'
        verbose_name_plural = 'Leave Requests'

    def _create_report(self, status, reviewer, comments=None):
        application = self.application
        LeaveReport.objects.create(
            status=status,
            leave_request=self,
            employee=application.employee,
            leave_type=application.leave_type,
            start_date=application.date_filed,
            end_date=(application.date_filed + timezone.timedelta(days=application.number_of_days - 1))
                     if status == 'approved' else application.date_filed,
            number_of_days=application.number_of_days,
            location=application.vacation_location or application.sick_location or 'N/A',
            date_filed=application.date_filed,
            approved_by=reviewer,
            approved_at=self.reviewed_at,
            review_comments=comments or ''
        )

    def approve(self, reviewer):
        self.status = 'approved'
        self.reviewer = reviewer
        self.reviewed_at = timezone.now()
        self.save()
        self.application.status = 'approved'
        self.application.save()

        # Use helper
        self._create_report('approved', reviewer)

    def deny(self, reviewer, comments=''):
        self.status = 'denied'
        self.reviewer = reviewer
        self.reviewed_at = timezone.now()
        self.review_comments = comments
        self.save()
        self.application.status = 'rejected'
        self.application.save()

        # Use helper
        self._create_report('rejected', reviewer, comments)

    @property
    def is_editable(self):
        return self.status == 'pending'

    def __str__(self):
        return f"{self.application.employee.full_name} - {self.status}"


# ----------------- Leave Report -----------------
class LeaveReport(models.Model):
    STATUS_CHOICES = [('approved', 'Approved'), ('rejected', 'Rejected')]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    leave_request = models.OneToOneField(LeaveRequest, on_delete=models.CASCADE, related_name='report')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_reports')
    leave_type = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    number_of_days = models.PositiveIntegerField()
    location = models.CharField(max_length=50)
    date_filed = models.DateField()
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    approved_at = models.DateTimeField(null=True, blank=True) 
    review_comments = models.TextField(blank=True) 
    reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-approved_at']
        verbose_name = 'Leave Report'
        verbose_name_plural = 'Leave Reports'

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type} Report"

    @classmethod
    def create_from_leave_request(cls, leave_request):
        application = leave_request.application
        return cls.objects.create(
            leave_request=leave_request,
            employee=leave_request.application.employee,
            leave_type=application.leave_type,
            number_of_days=application.number_of_days,
            location=application.vacation_location or application.sick_location or 'N/A',
            date_filed=application.date_filed,
            approved_by=leave_request.reviewer,
            approved_at=leave_request.reviewed_at
        )


