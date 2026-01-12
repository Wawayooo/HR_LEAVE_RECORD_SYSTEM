from rest_framework import serializers
from .models import *
from django.core.validators import MinValueValidator, MaxValueValidator


# ==================== Department Serializer ====================
class DepartmentSerializer(serializers.ModelSerializer):
    employee_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = ['id', 'code', 'name', 'description', 'created_at', 'employee_count']
        read_only_fields = ['created_at']
    
    def get_employee_count(self, obj):
        """Return count of active employees in this department"""
        return Employee.objects.filter(department=obj, is_active=True).count()


# ==================== Position Serializer ====================
class PositionSerializer(serializers.ModelSerializer):
    occupied = serializers.SerializerMethodField()
    occupied_by = serializers.SerializerMethodField()
    
    class Meta:
        model = Position
        fields = ['id', 'code', 'title', 'description', 'created_at', 'occupied', 'occupied_by']
        read_only_fields = ['created_at']
    
    def get_occupied(self, obj):
        """Check if position is currently occupied by an active employee"""
        return Employee.objects.filter(position=obj, is_active=True).exists()
    
    def get_occupied_by(self, obj):
        """Return employee info if position is occupied"""
        employee = Employee.objects.filter(position=obj, is_active=True).first()
        if employee:
            return {
                'id': employee.id,
                'name': employee.full_name,
                'employee_id': employee.employee_id
            }
        return None


# ==================== Employee Serializer ====================
class EmployeeSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_code = serializers.CharField(source='department.code', read_only=True)
    position_title = serializers.CharField(source='position.title', read_only=True)
    position_code = serializers.CharField(source='position.code', read_only=True)
    photo_url = serializers.SerializerMethodField()
    company_id = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'company_id', 'full_name', 'gender', 'age',
            'height', 'weight', 'department', 'department_name', 'department_code',
            'position', 'position_title', 'position_code', 'photo', 'photo_url',
            'motto_in_life', 'is_active', 'date_created', 'updated_at'
        ]
        read_only_fields = ['employee_id', 'date_created', 'updated_at']

    def get_photo_url(self, obj):
        """Return full URL for employee photo"""
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None
    
    def validate_age(self, value):
        """Validate age is within reasonable range"""
        if value < 18:
            raise serializers.ValidationError("Employee must be at least 18 years old")
        if value > 100:
            raise serializers.ValidationError("Please enter a valid age")
        return value
    
    def validate_height(self, value):
        """Validate height is within reasonable range (in cm)"""
        if value < 100:
            raise serializers.ValidationError("Height must be at least 100 cm")
        if value > 250:
            raise serializers.ValidationError("Height cannot exceed 250 cm")
        return value
    
    def validate_weight(self, value):
        """Validate weight is within reasonable range (in kg)"""
        if value < 30:
            raise serializers.ValidationError("Weight must be at least 30 kg")
        if value > 300:
            raise serializers.ValidationError("Weight cannot exceed 300 kg")
        return value
    
    def validate_position(self, value):
        """Allow multiple employees to share the same position"""
        return value



# ==================== Leave Application Serializer ====================
class LeaveApplicationSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_id_display = serializers.CharField(source='employee.employee_id', read_only=True)
    employee_photo_url = serializers.SerializerMethodField()
    
    department_name = serializers.CharField(source='employee.department.name', read_only=True)
    position_title = serializers.CharField(source='employee.position.title', read_only=True)
    
    class Meta:
        model = LeaveApplication
        fields = [
            'id', 'employee', 'employee_name', 'employee_id_display', 'employee_photo_url',
            'leave_type', 'vacation_location', 'sick_location',
            'number_of_days', 'reason', 'date_filed', 'status', 'department_name', 'position_title'
        ]
        read_only_fields = ['date_filed', 'status']
    
    def get_employee_photo_url(self, obj):
        """Return employee photo URL"""
        if obj.employee and obj.employee.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.employee.photo.url)
            return obj.employee.photo.url
        return None
    
    def validate_number_of_days(self, value):
        """Validate number of days doesn't exceed maximum allowed"""
        if value > 15:
            raise serializers.ValidationError(
                "Maximum leave application is 15 days per request"
            )
        if value < 1:
            raise serializers.ValidationError(
                "Number of days must be at least 1"
            )
        return value
    
    def validate(self, data):
        """Validate leave application based on leave type"""
        leave_type = data.get('leave_type')
        
        if leave_type == 'vacation' and not data.get('vacation_location'):
            raise serializers.ValidationError({
                'vacation_location': 'Vacation location is required for vacation leave'
            })
        
        if leave_type == 'sick' and not data.get('sick_location'):
            raise serializers.ValidationError({
                'sick_location': 'Sick location is required for sick leave'
            })
        
        return data


# ==================== Leave Request Serializer ====================
class LeaveRequestSerializer(serializers.ModelSerializer):
    application = LeaveApplicationSerializer(read_only=True)
    reviewer_name = serializers.CharField(source='reviewer.username', read_only=True, allow_null=True)

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'application', 'reviewer', 'reviewer_name',
            'reviewed_at', 'review_comments', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'reviewed_at']


# ==================== Leave Report Serializer ====================
class LeaveReportSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    employee_photo_url = serializers.SerializerMethodField()
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True, allow_null=True)
    
    department_name = serializers.CharField(source='employee.department.name', read_only=True)
    position_title = serializers.CharField(source='employee.position.title', read_only=True)
    reason = serializers.CharField(source='employee.reason', read_only=True)

    class Meta:
        model = LeaveReport
        fields = [
            'id', 'leave_request', 'employee', 'employee_name', 'employee_id', 'employee_photo_url',
            'leave_type', 'start_date', 'end_date', 'number_of_days',
            'location', 'date_filed', 'approved_by', 'approved_by_name',
            'approved_at', 'created_at', 'status',
            'review_comments', 'reviewed_at', 'department_name', 'position_title', 'reason'
        ]
        read_only_fields = ['created_at']
    
    def get_employee_photo_url(self, obj):
        """Return employee photo URL"""
        if obj.employee and obj.employee.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.employee.photo.url)
            return obj.employee.photo.url
        return None


# ==================== HR User Serializer ====================
class HRUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = HRUser
        fields = [
            'id',
            'username',
            'full_name',
            'gender',
            'height',
            'weight',
            'age',
            'photo',
            'photo_url',
            'is_hr',
            'password'
        ]
        read_only_fields = ['id', 'is_hr', 'username', 'photo_url']
    
    def get_photo_url(self, obj):
        """Return full URL for HR user photo"""
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None
    
    def validate_password(self, value):
        """Validate password if provided"""
        if value and len(value) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters long")
        return value
    
    def validate_age(self, value):
        """Validate age is within reasonable range"""
        if value and (value < 18 or value > 100):
            raise serializers.ValidationError("Please enter a valid age (18-100)")
        return value
    
    def validate_height(self, value):
        """Validate height is within reasonable range"""
        if value and (value < 100 or value > 250):
            raise serializers.ValidationError("Please enter a valid height (100-250 cm)")
        return value
    
    def validate_weight(self, value):
        """Validate weight is within reasonable range"""
        if value and (value < 30 or value > 300):
            raise serializers.ValidationError("Please enter a valid weight (30-300 kg)")
        return value

    def update(self, instance, validated_data):
        """Handle HR user update including password"""
        # Handle password update on the related User
        password = validated_data.pop('password', None)
        if password and password.strip():
            instance.user.set_password(password)
            instance.user.save()

        # Update HRUser fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance