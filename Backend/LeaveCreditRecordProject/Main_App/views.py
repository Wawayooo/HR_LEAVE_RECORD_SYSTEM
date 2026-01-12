from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from .models import *
from .serializers import *

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.hashers import check_password
from .models import AccessKey

import json
from django.utils import timezone
from rest_framework.response import Response

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.decorators import action

from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth.decorators import login_required

# ============= ViewSets with Full CRUD =============

MAX_ANNUAL_LEAVE_DAYS = 15

class DepartmentViewSet(viewsets.ModelViewSet):
    """
    Full CRUD operations for Departments:
    - GET /api/departments/ - List all departments
    - POST /api/departments/ - Create new department
    - GET /api/departments/{id}/ - Retrieve single department
    - PUT /api/departments/{id}/ - Update department
    - PATCH /api/departments/{id}/ - Partial update
    - DELETE /api/departments/{id}/ - Delete department
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.AllowAny]

    def destroy(self, request, *args, **kwargs):
        """Delete department with safety check"""
        department = self.get_object()
        employee_count = department.employees.count()
        
        if employee_count > 0:
            return Response({
                'success': False,
                'message': f'Cannot delete department. {employee_count} employee(s) are assigned to this department.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        department.delete()
        return Response({
            'success': True,
            'message': 'Department deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def employees(self, request, pk=None):
        """Get all employees in this department"""
        department = self.get_object()
        employees = department.employees.filter(is_active=True)
        serializer = EmployeeSerializer(employees, many=True, context={'request': request})
        return Response(serializer.data)


class PositionViewSet(viewsets.ModelViewSet):
    """
    Full CRUD operations for Positions:
    - GET /api/positions/ - List all positions
    - POST /api/positions/ - Create new position
    - GET /api/positions/{id}/ - Retrieve single position
    - PUT /api/positions/{id}/ - Update position
    - PATCH /api/positions/{id}/ - Partial update
    - DELETE /api/positions/{id}/ - Delete position
    """
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = [permissions.AllowAny]

    def destroy(self, request, *args, **kwargs):
        """Delete position with safety check"""
        position = self.get_object()
        employee_count = position.employees.count()
        
        if employee_count > 0:
            return Response({
                'success': False,
                'message': f'Cannot delete position. {employee_count} employee(s) hold this position.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        position.delete()
        return Response({
            'success': True,
            'message': 'Position deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def employees(self, request, pk=None):
        """Get all employees in this position"""
        position = self.get_object()
        employees = position.employees.filter(is_active=True)
        serializer = EmployeeSerializer(employees, many=True, context={'request': request})
        return Response(serializer.data)


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Employee.objects.all()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department_id=department)
        position = self.request.query_params.get('position')
        if position:
            queryset = queryset.filter(position_id=position)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            employee = serializer.save(is_active=True)
            return Response({
                'success': True,
                'message': 'Employee registered successfully!',
                'data': EmployeeSerializer(employee, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            employee = serializer.save()
            return Response({
                'success': True,
                'message': 'Employee updated successfully!',
                'data': EmployeeSerializer(employee, context={'request': request}).data
            })
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Soft delete (deactivate) employee"""
        employee = self.get_object()
        employee.is_active = False
        employee.save()
        return Response({
            'success': True,
            'message': 'Employee deactivated',
            'data': EmployeeSerializer(employee, context={'request': request}).data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        employee = self.get_object()
        employee.is_active = True
        employee.save()
        return Response({
            'success': True,
            'message': 'Employee activated successfully',
            'data': EmployeeSerializer(employee, context={'request': request}).data
        })

    @action(detail=False, methods=['get'])
    def by_department(self, request):
        department_code = request.query_params.get('department')
        employees = self.queryset.filter(is_active=True)
        if department_code:
            employees = employees.filter(department__code=department_code)
        serializer = self.get_serializer(employees, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def inactive(self, request):
        inactive_employees = self.queryset.filter(is_active=False)
        serializer = self.get_serializer(inactive_employees, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def leave_history(self, request, pk=None):
        employee = self.get_object()
        leave_applications = LeaveApplication.objects.filter(employee=employee)
        serializer = LeaveApplicationSerializer(leave_applications, many=True)
        return Response(serializer.data)

    @method_decorator(csrf_exempt, name='dispatch') 
    @action(
        detail=False,
        methods=['post'],
        url_path='verify-employee',
        permission_classes=[AllowAny]
    )
    @csrf_exempt  # optional if you want to skip CSRF
    def verify_employee(self, request):
        employee_code = request.data.get('employee_id', '').strip()
        if not employee_code:
            return Response({'success': False, 'message': 'Employee ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            employee = Employee.objects.get(employee_id=employee_code, is_active=True)
            current_year = timezone.now().year
            balance, _ = EmployeeLeaveBalance.objects.get_or_create(
                employee=employee,
                year=current_year,
                defaults={'remaining_days': 15}
            )
            return Response({
                'success': True,
                'employee_id': employee.id,
                'employee_code': employee.employee_id,
                'full_name': employee.full_name,
                'remaining_days': balance.remaining_days,
                'year': current_year
            })
        except Employee.DoesNotExist:
            return Response({'success': False, 'message': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)


class LeaveApplicationViewSet(viewsets.ModelViewSet):
    """
    Full CRUD operations for Leave Applications
    """
    queryset = LeaveApplication.objects.all()
    serializer_class = LeaveApplicationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        """Create leave application with validation"""
        employee_id = request.data.get('employee')
        number_of_days = request.data.get('number_of_days')
        
        # Validate employee exists
        try:
            employee = Employee.objects.get(id=employee_id, is_active=True)
        except Employee.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Employee not found in records. Please verify your name.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get leave balance
        current_year = timezone.now().year
        try:
            balance = EmployeeLeaveBalance.objects.get(
                employee=employee,
                year=current_year
            )
        except EmployeeLeaveBalance.DoesNotExist:
            # Create default balance if doesn't exist
            balance = EmployeeLeaveBalance.objects.create(
                employee=employee,
                year=current_year,
                remaining_days=15
            )
        
        # Validate number of days
        try:
            days = int(number_of_days)
        except (ValueError, TypeError):
            return Response({
                'success': False,
                'message': 'Invalid number of days'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if exceeds 15 days limit
        if days > 15:
            return Response({
                'success': False,
                'message': 'Maximum leave application is 15 days per request'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check remaining days
        if days > balance.remaining_days:
            return Response({
                'success': False,
                'message': f'Insufficient leave balance. You only have {balance.remaining_days} days remaining for {current_year}.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Proceed with creation
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            application = serializer.save()
            
            # Deduct days from balance
            balance.deduct_days(days)
            
            # Automatically create a leave request
            LeaveRequest.objects.create(application=application)
            
            return Response({
                'success': True,
                'message': f'Leave application submitted successfully! {balance.remaining_days} days remaining.',
                'data': serializer.data,
                'remaining_days': balance.remaining_days
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """Update leave application"""
        instance = self.get_object()
        
        # Check if already approved/rejected
        if instance.status != 'pending':
            return Response({
                'success': False,
                'message': f'Cannot update {instance.status} leave application'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete leave application and restore leave balance"""
        application = self.get_object()
        
        # Only allow deletion if pending
        if application.status != 'pending':
            return Response({
                'success': False,
                'message': f'Cannot delete {application.status} leave application'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Restore the leave days before deletion
        try:
            current_year = timezone.now().year
            balance = EmployeeLeaveBalance.objects.get(
                employee=application.employee,
                year=current_year
            )
            # Add back the days
            balance.remaining_days += application.number_of_days
            balance.save()
        except EmployeeLeaveBalance.DoesNotExist:
            pass  # Balance doesn't exist, nothing to restore
        
        application.delete()
        return Response({
            'success': True,
            'message': 'Leave application deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)

from rest_framework import permissions

class IsHRUser(permissions.BasePermission):
    """
    Custom permission to only allow HR users to perform certain actions.
    Assumes you have an HRUser model linked to Django's User.
    """
    def has_permission(self, request, view):
        # User must be authenticated and have an HRUser profile marked as HR
        return (
            request.user.is_authenticated and 
            hasattr(request.user, 'hruser') and 
            request.user.hruser.is_hr
        )

class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsHRUser]

    @action(detail=False, methods=['get'])
    def pending(self, request):
        requests = self.queryset.filter(status='pending')
        serializer = self.get_serializer(requests, many=True)
        return Response({'success': True, 'data': serializer.data})

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        leave_request = self.get_object()
        if leave_request.status != 'pending':
            return Response({'success': False, 'message': f'Already {leave_request.status}'}, status=400)

        leave_request.status = 'approved'
        leave_request.reviewer = request.user if request.user.is_authenticated else None
        leave_request.reviewed_at = timezone.now()
        leave_request.save()

        leave_request.application.status = 'approved'
        leave_request.application.save()

        LeaveReport.create_from_leave_request(leave_request)

        return Response({
            'success': True,
            'message': 'Leave request approved successfully',
            'data': LeaveRequestSerializer(leave_request, context={'request': request}).data
        })

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        leave_request = self.get_object()

        # Check if already processed
        if leave_request.status != 'pending':
            return Response({'success': False, 'message': f'Already {leave_request.status}'}, status=400)

        # Reject the leave request
        leave_request.status = 'denied'
        leave_request.reviewer = request.user if request.user.is_authenticated else None
        leave_request.reviewed_at = timezone.now()
        leave_request.review_comments = request.data.get('comments', '')
        leave_request.save()

        # Update application status
        leave_request.application.status = 'rejected'
        leave_request.application.save()

        # === Add back days to employee leave balance, capped at MAX_ANNUAL_LEAVE_DAYS ===
        from datetime import date
        current_year = date.today().year
        days_requested = leave_request.application.number_of_days or 0
        employee = leave_request.application.employee

        # Get or create the EmployeeLeaveBalance for this year
        balance, created = EmployeeLeaveBalance.objects.get_or_create(
            employee=employee,
            year=current_year,
            defaults={'remaining_days': MAX_ANNUAL_LEAVE_DAYS}  # default if balance did not exist
        )

        # Add days but do not exceed MAX_ANNUAL_LEAVE_DAYS
        balance.remaining_days = min(balance.remaining_days + days_requested, MAX_ANNUAL_LEAVE_DAYS)
        balance.save()
        # ================================================================

        return Response({
            'success': True,
            'message': f'Leave request rejected and {days_requested} day(s) returned to balance',
            'data': LeaveRequestSerializer(leave_request, context={'request': request}).data
        })



class LeaveReportViewSet(viewsets.ModelViewSet):
    queryset = LeaveReport.objects.all()
    serializer_class = LeaveReportSerializer
    permission_classes = [permissions.IsAuthenticated, IsHRUser]

    @action(detail=False, methods=['get'])
    def recent(self, request):
        limit = int(request.query_params.get('limit', 10))
        reports = self.get_queryset()[:limit]
        serializer = self.get_serializer(reports, many=True)
        return Response({'success': True, 'data': serializer.data})

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        from django.db.models import Count
        stats = self.get_queryset().values('leave_type').annotate(count=Count('leave_type'))
        return Response({'success': True, 'total_reports': self.get_queryset().count(), 'by_leave_type': stats})



# ============= API Views =============

@csrf_exempt
def verify_key(request):
    if request.method == "POST":
        data = json.loads(request.body)
        input_key = data.get("key", "")

        try:
            access_key = AccessKey.objects.latest('created_at')
            if check_password(input_key, access_key.key_hash):
                request.session['secret_authenticated'] = True
                return JsonResponse({"success": True})
        except AccessKey.DoesNotExist:
            pass

        return JsonResponse({"success": False})



@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def dashboard_stats(request):
    """Get dashboard statistics"""
    total_employees = Employee.objects.filter(is_active=True).count()
    inactive_employees = Employee.objects.filter(is_active=False).count()
    pending_leaves = LeaveRequest.objects.filter(status='pending').count()
    approved_leaves = LeaveRequest.objects.filter(status='approved').count()
    denied_leaves = LeaveRequest.objects.filter(status='denied').count()
    
    # Employees by department
    departments = Department.objects.all()
    dept_stats = []
    for dept in departments:
        count = Employee.objects.filter(department=dept, is_active=True).count()
        dept_stats.append({
            'code': dept.code,
            'name': dept.name,
            'count': count
        })

    return Response({
        'total_employees': total_employees,
        'inactive_employees': inactive_employees,
        'pending_leaves': pending_leaves,
        'approved_leaves': approved_leaves,
        'denied_leaves': denied_leaves,
        'departments': dept_stats
    })

# ============= Template Views =============

def appointment_form_view(request):
    return render(request, 'leave_requests_interface.html')

def starting_view(request):
    return render(request, "index.html")

@login_required
def HR_dash_view(request):
    return render(request, "Dashboard.html")

from rest_framework import viewsets
from .models import HRUser
from .serializers import HRUserSerializer
from rest_framework.permissions import IsAuthenticated
from django.http import Http404

# views.py
from rest_framework import viewsets
from django.http import Http404
from .models import HRUser
from .serializers import HRUserSerializer

from rest_framework.permissions import IsAuthenticated

class HRUserViewSet(viewsets.ModelViewSet):
    queryset = HRUser.objects.all()
    serializer_class = HRUserSerializer
    permission_classes = [IsAuthenticated]  # ✅ require login
    lookup_field = 'username'

    def get_object(self):
        username = self.kwargs.get(self.lookup_field)
        return HRUser.objects.get(user__username=username)

from django.contrib.auth import authenticate, login

@csrf_exempt
def hr_login(request):
    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None and hasattr(user, 'hruser') and user.hruser.is_hr:
            login(request, user)  # sets session
            return JsonResponse({
                "success": True,
                "message": "Login successful",
                "username": user.username,
                "full_name": user.hruser.full_name,
                "photo_url": user.hruser.photo.url if user.hruser.photo else None
            })
        else:
            return JsonResponse({"success": False, "message": "Invalid credentials"})

from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse

@ensure_csrf_cookie
def csrf(request):
    return JsonResponse({'detail': 'CSRF cookie set'})
