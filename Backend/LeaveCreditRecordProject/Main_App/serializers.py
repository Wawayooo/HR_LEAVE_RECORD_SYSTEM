from rest_framework import serializers
from .models import *
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password


class DepartmentSerializer(serializers.ModelSerializer):
    employee_count = serializers.SerializerMethodField()
    dean_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = ['id', 'code', 'name', 'description', 'created_at', 'employee_count', 'dean_name']
        read_only_fields = ['created_at']
    
    def get_employee_count(self, obj):
        return Employee.objects.filter(department=obj, is_active=True).count()
    
    def get_dean_name(self, obj):
        dean = Dean.objects.filter(department=obj, is_active=True).first()
        return dean.full_name if dean else None


class PositionSerializer(serializers.ModelSerializer):
    occupied = serializers.SerializerMethodField()
    occupied_by = serializers.SerializerMethodField()
    
    class Meta:
        model = Position
        fields = ['id', 'code', 'title', 'description', 'created_at', 'occupied', 'occupied_by']
        read_only_fields = ['created_at']
    
    def get_occupied(self, obj):
        return Employee.objects.filter(position=obj, is_active=True).exists()
    
    def get_occupied_by(self, obj):
        employee = Employee.objects.filter(position=obj, is_active=True).first()
        if employee:
            return {
                'id': employee.id,
                'name': employee.full_name,
                'employee_id': employee.employee_id
            }
        return None


class DeanSerializer(serializers.ModelSerializer):
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        required=False
    )
    
    username = serializers.CharField(source='user.username', required=False)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_code = serializers.CharField(source='department.code', read_only=True)
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Dean
        fields = [
            'id', 'username', 'full_name', 'department', 'department_name',
            'department_code', 'gender', 'height', 'weight', 'age',
            'photo', 'photo_url', 'is_dean', 'is_active',
            'created_at', 'updated_at', 'password'
        ]
        read_only_fields = ['id', 'is_dean', 'created_at', 'updated_at', 'photo_url']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        password = validated_data.pop('password', None)

        if 'username' in user_data:
            new_username = user_data['username']
            if new_username != instance.user.username:
                if User.objects.filter(username=new_username).exclude(id=instance.user.id).exists():
                    raise serializers.ValidationError({"username": "Username already exists"})
                instance.user.username = new_username
                instance.user.save()

        if password:
            instance.user.set_password(password)
            instance.user.save()

        validated_data['is_active'] = True

        return super().update(instance, validated_data)
    
    def get_photo_url(self, obj):
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None
    
    def validate_password(self, value):
        if value and len(value) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters long")
        return value
    
    def validate_age(self, value):
        if value and (value < 18 or value > 100):
            raise serializers.ValidationError("Please enter a valid age (18-100)")
        return value
    
    def validate_height(self, value):
        if value and (value < 100 or value > 250):
            raise serializers.ValidationError("Please enter a valid height (100-250 cm)")
        return value
    
    def validate_weight(self, value):
        if value and (value < 30 or value > 300):
            raise serializers.ValidationError("Please enter a valid weight (30-300 kg)")
        return value

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
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None
    
    def validate_age(self, value):
        if value < 18:
            raise serializers.ValidationError("Employee must be at least 18 years old")
        if value > 100:
            raise serializers.ValidationError("Please enter a valid age")
        return value
    
    def validate_height(self, value):
        if value < 100:
            raise serializers.ValidationError("Height must be at least 100 cm")
        if value > 250:
            raise serializers.ValidationError("Height cannot exceed 250 cm")
        return value
    
    def validate_weight(self, value):
        if value < 30:
            raise serializers.ValidationError("Weight must be at least 30 kg")
        if value > 300:
            raise serializers.ValidationError("Weight cannot exceed 300 kg")
        return value
    
    def validate_position(self, value):
        return value


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
        if obj.employee and obj.employee.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.employee.photo.url)
            return obj.employee.photo.url
        return None
    
    def validate_number_of_days(self, value):
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

class LeaveRequestSerializer(serializers.ModelSerializer):
    application = LeaveApplicationSerializer(read_only=True)
    dean_reviewer_name = serializers.CharField(source='dean_reviewer.full_name', read_only=True, allow_null=True)
    dean_reviewer_username = serializers.CharField(source='dean_reviewer.user.username', read_only=True, allow_null=True)
    hr_reviewer_name = serializers.CharField(source='hr_reviewer.full_name', read_only=True, allow_null=True)
    status_display = serializers.SerializerMethodField()
    is_pending_dean = serializers.BooleanField(source='is_pending_dean_approval', read_only=True)
    is_pending_hr = serializers.BooleanField(source='is_pending_hr_approval', read_only=True)

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'application', 

            'dean_reviewer', 'dean_reviewer_name', 'dean_reviewer_username',
            'dean_reviewed_at', 'dean_comments',

            'hr_reviewer', 'hr_reviewer_name',
            'hr_reviewed_at', 'hr_comments',

            'status', 'status_display', 'is_pending_dean', 'is_pending_hr',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'dean_reviewed_at', 'hr_reviewed_at']
    
    def get_status_display(self, obj):
        status_map = {
            'pending': 'Pending Dean Approval',
            'dean_approved': 'Pending HR Approval',
            'dean_denied': 'Denied by Dean',
            'approved': 'Approved by HR',
            'denied': 'Denied by HR'
        }
        return status_map.get(obj.status, obj.status)


class LeaveReportSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    employee_photo_url = serializers.SerializerMethodField()

    dean_reviewer_name = serializers.CharField(source='dean_reviewer.username', read_only=True, allow_null=True)
    dean_status_display = serializers.CharField(source='get_dean_status_display', read_only=True)
    
    hr_reviewer_name = serializers.CharField(source='hr_reviewer.full_name', read_only=True)
    
    hr_status_display = serializers.CharField(source='get_hr_status_display', read_only=True)

    department_name = serializers.CharField(source='employee.department.name', read_only=True)
    position_title = serializers.CharField(source='employee.position.title', read_only=True)

    reason = serializers.SerializerMethodField()

    class Meta:
        model = LeaveReport
        fields = [
            'id',
            'leave_request',
            'employee', 'employee_name', 'employee_id', 'employee_photo_url',
            'leave_type', 'number_of_days',
            'location', 'date_filed',
            'dean_status', 'dean_status_display', 'dean_reviewer_name', 'dean_reviewed_at', 'dean_comments',
            'hr_status', 'hr_status_display', 'hr_reviewer_name', 'hr_reviewed_at', 'hr_comments',
            'department_name', 'position_title', 'reason',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_employee_photo_url(self, obj):
        if obj.employee and getattr(obj.employee, "photo", None):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.employee.photo.url)
            return obj.employee.photo.url
        return None

    def get_reason(self, obj):
        if obj.leave_request and obj.leave_request.application:
            return obj.leave_request.application.reason
        return None


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
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None
    
    def validate_password(self, value):
        if value and len(value) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters long")
        return value
    
    def validate_age(self, value):
        if value and (value < 18 or value > 100):
            raise serializers.ValidationError("Please enter a valid age (18-100)")
        return value
    
    def validate_height(self, value):
        if value and (value < 100 or value > 250):
            raise serializers.ValidationError("Please enter a valid height (100-250 cm)")
        return value
    
    def validate_weight(self, value):
        if value and (value < 30 or value > 300):
            raise serializers.ValidationError("Please enter a valid weight (30-300 kg)")
        return value

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password and password.strip():
            instance.user.set_password(password)
            instance.user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance