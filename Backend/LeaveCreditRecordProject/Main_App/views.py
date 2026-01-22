from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.db import transaction

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from django.views.decorators.http import require_http_methods

import json
from django.http import JsonResponse

from .models import *
from .serializers import *

MAX_ANNUAL_LEAVE_DAYS = 15


class IsHRUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            hasattr(request.user, 'hruser') and 
            request.user.hruser.is_hr
        )


class IsDean(permissions.BasePermission):
    def has_permission(self, request, view):
            
        return (
            request.user.is_authenticated and 
            hasattr(request.user, 'dean_profile') and 
            request.user.dean_profile.is_dean
        )

class IsHROrDean(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        
        is_hr = (
            hasattr(user, 'hruser') and 
            getattr(user.hruser, 'is_hr', False)
        )
        
        is_dean = (
            hasattr(user, 'dean_profile') and 
            getattr(user.dean_profile, 'is_dean', False)
        )
        
        in_hr_group = user.groups.filter(name='HR').exists()
        
        return is_hr or is_dean or in_hr_group
    

def test_approve(request, pk):
    return JsonResponse({'ok': True, 'pk': pk})

class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsHROrDean]

    def get_queryset(self):
        user = self.request.user
        queryset = LeaveRequest.objects.all()

        if hasattr(user, 'dean_profile'):
            dean = user.dean_profile
            queryset = queryset.filter(
                application__employee__department=dean.department
            )

            view_type = self.request.query_params.get('view')

            if view_type == 'requests':
                queryset = queryset.filter(status='pending', is_archived=False)
            elif view_type == 'reports':
                queryset = queryset.filter(
                    status__in=['dean_approved', 'dean_denied', 'approved', 'denied']
                )
            else:
                queryset = queryset.exclude(status='pending').filter(is_archived=False)

        elif hasattr(user, 'hruser') or user.groups.filter(name='HR').exists():
            view_type = self.request.query_params.get('view')

            if view_type == 'dashboard':
                queryset = self.hr_dash_queryset().filter(is_archived=False)
            elif view_type == 'reports':
                queryset = queryset.filter(
                    status__in=['dean_approved', 'approved', 'denied']
                )
            else:
                queryset = queryset.exclude(status='pending').filter(is_archived=False)

        return queryset

    
    def hr_dash_queryset(self):
        return LeaveRequest.objects.filter(
            status='dean_approved'
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"detail": "Leave request permanently deleted."}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def pending_dean(self, request):
        requests = self.get_queryset().filter(status='pending')
        serializer = self.get_serializer(requests, many=True)
        return Response({'success': True, 'data': serializer.data})

    @action(detail=False, methods=['get'])
    def pending_hr(self, request):
        if not (hasattr(request.user, 'hruser') or request.user.groups.filter(name='HR').exists()):
            return Response({'success': False, 'message': 'HR only'}, status=403)
        
        requests = LeaveRequest.objects.filter(status='dean_approved')
        
        serializer = self.get_serializer(requests, many=True)
        return Response({'success': True, 'data': serializer.data})

    @action(detail=True, methods=['post'])
    def dean_approve(self, request, pk=None):
        try:
            leave_request = LeaveRequest.objects.get(pk=pk)
        except LeaveRequest.DoesNotExist:
            return Response({'success': False, 'message': 'Leave request not found'}, status=404)

        if not hasattr(request.user, 'dean_profile'):
            return Response({'success': False, 'message': 'Dean only'}, status=403)

        dean = request.user.dean_profile

        if leave_request.application.employee.department != dean.department:
            return Response({
                'success': False,
                'message': 'You can only approve requests from your department'
            }, status=403)

        if leave_request.status != 'pending':
            return Response({
                'success': False,
                'message': f'Request already {leave_request.status}'
            }, status=400)

        try:
            leave_request.dean_approve(dean)
            return Response({
                'success': True,
                'message': 'Leave request approved and forwarded to HR',
                'data': self.get_serializer(leave_request).data
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=400)


    @action(detail=True, methods=['post'])
    def dean_deny(self, request, pk=None):
        try:
            leave_request = LeaveRequest.objects.get(pk=pk)
        except LeaveRequest.DoesNotExist:
            return Response({'success': False, 'message': 'Leave request not found'}, status=404)

        if not hasattr(request.user, 'dean_profile'):
            return Response({'success': False, 'message': 'Dean only'}, status=403)

        dean = request.user.dean_profile

        if leave_request.application.employee.department != dean.department:
            return Response({
                'success': False,
                'message': 'You can only deny requests from your department'
            }, status=403)

        if leave_request.status != 'pending':
            return Response({
                'success': False,
                'message': f'Request already {leave_request.status}'
            }, status=400)

        comments = request.data.get('comments', '')

        try:
            current_year = timezone.now().year
            balance, _ = EmployeeLeaveBalance.objects.get_or_create(
                employee=leave_request.application.employee,
                year=current_year,
                defaults={'remaining_days': MAX_ANNUAL_LEAVE_DAYS}
            )
            days = leave_request.application.number_of_days
            balance.remaining_days = min(balance.remaining_days + days, MAX_ANNUAL_LEAVE_DAYS)
            balance.save()

            leave_request.dean_deny(dean, comments)

            return Response({
                'success': True,
                'message': f'Leave request denied. {days} days restored to employee balance.',
                'data': self.get_serializer(leave_request).data
            })
        except Exception as e:
            #print("Dean deny error:", e)
            return Response({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=400)

    @action(detail=True, methods=['post'])
    def hr_approve(self, request, pk=None):
        if not (hasattr(request.user, 'hruser') or request.user.groups.filter(name='HR').exists()):
            return Response({'success': False, 'message': 'HR only'}, status=403)
        
        leave_request = self.get_object()
        
        if leave_request.status != 'dean_approved':
            return Response({
                'success': False,
                'message': 'Request must be dean-approved first'
            }, status=400)
        
        comments = request.data.get('comments', '')
        
        try:
            leave_request.hr_approve(request.user)
            if comments:
                leave_request.hr_comments = comments
                leave_request.save()
            
            return Response({
                'success': True,
                'message': 'Leave request approved by HR',
                'data': self.get_serializer(leave_request).data
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=400)

    @action(detail=True, methods=['post'])
    def hr_deny(self, request, pk=None):
        if not (hasattr(request.user, 'hruser') or request.user.groups.filter(name='HR').exists()):
            return Response({'success': False, 'message': 'HR only'}, status=403)
        
        leave_request = self.get_object()
        
        if leave_request.status != 'dean_approved':
            return Response({
                'success': False,
                'message': 'Request must be dean-approved first'
            }, status=400)
        
        comments = request.data.get('comments', '')
        if not comments:
            return Response({
                'success': False,
                'message': 'Comments required for denial'
            }, status=400)
        
        try:
            current_year = timezone.now().year
            balance, _ = EmployeeLeaveBalance.objects.get_or_create(
                employee=leave_request.application.employee,
                year=current_year,
                defaults={'remaining_days': MAX_ANNUAL_LEAVE_DAYS}
            )
            days = leave_request.application.number_of_days
            balance.remaining_days = min(balance.remaining_days + days, MAX_ANNUAL_LEAVE_DAYS)
            balance.save()
            
            leave_request.hr_deny(request.user, comments)
            
            return Response({
                'success': True,
                'message': f'Leave request denied by HR. {days} days restored to employee balance.',
                'data': self.get_serializer(leave_request).data
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=400)
            
    @action(detail=False, methods=['get'])
    def dean_approved(self, request):
        if not (hasattr(request.user, 'dean_profile') or 
                hasattr(request.user, 'hruser') or 
                request.user.groups.filter(name='HR').exists()):
            return Response({'success': False, 'message': 'Dean or HR only'}, status=403)

        queryset = LeaveRequest.objects.filter(status='dean_approved')
        
        if hasattr(request.user, 'dean_profile'):
            dean = request.user.dean_profile
            queryset = queryset.filter(application__employee__department=dean.department)

        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, 'data': serializer.data})


    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        if hasattr(request.user, 'dean_profile'):
            return self.dean_approve(request, pk)
        elif hasattr(request.user, 'hruser') or request.user.groups.filter(name='HR').exists():
            return self.hr_approve(request, pk)
        return Response({'success': False, 'message': 'Unauthorized'}, status=403)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        if hasattr(request.user, 'dean_profile'):
            return self.dean_deny(request, pk)
        elif hasattr(request.user, 'hruser') or request.user.groups.filter(name='HR').exists():
            return self.hr_deny(request, pk)
        return Response({'success': False, 'message': 'Unauthorized'}, status=403)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        if not (hasattr(request.user, 'hruser') or request.user.groups.filter(name='HR').exists()):
            return Response({
                'success': False, 
                'message': 'Only HR users can archive leave requests'
            }, status=403)
        
        leave_request = self.get_object()
        
        if leave_request.status not in ['approved', 'denied']:
            return Response({
                'success': False,
                'message': f'Cannot archive request with status \"{leave_request.status}\". Only approved or denied requests can be archived.'
            }, status=400)
            
        try:
            archive = LeaveRequestArchive.archive_leave_request(leave_request)

            leave_request.is_archived = True
            leave_request.save(update_fields=['is_archived'])

            return Response({
                'success': True,
                'message': 'Leave request archived successfully',
                'data': {
                    'archive_id': archive.id,
                    'employee_name': archive.employee_name,
                    'final_status': archive.final_status,
                    'archived_at': archive.archived_at,
                    'is_archived': leave_request.is_archived
                }
            })

        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error archiving leave request: {str(e)}'
            }, status=400)


    @action(detail=False, methods=['post'])
    def archive_all_processed(self, request):
        if not (hasattr(request.user, 'hruser') or request.user.groups.filter(name='HR').exists()):
            return Response({
                'success': False, 
                'message': 'Only HR can perform batch archiving'
            }, status=403)
        
        processed_requests = LeaveRequest.objects.filter(status__in=['approved', 'denied'])
        
        if hasattr(request.user, 'dean_profile'):
            dean = request.user.dean_profile
            processed_requests = processed_requests.filter(
                application__employee__department=dean.department
            )
        
        if not processed_requests.exists():
            return Response({
                'success': False,
                'message': 'No processed leave requests found to archive'
            }, status=404)
        
        try:
            from .models import LeaveRequestArchive
            archived_count = 0
            failed_count = 0
            archived_ids = []
            
            for leave_request in processed_requests:
                try:
                    archive = LeaveRequestArchive.archive_leave_request(leave_request)
                    archived_ids.append(archive.id)
                    archived_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    print(f"Failed to archive LeaveRequest {leave_request.id}: {str(e)}")
            
            return Response({
                'success': True,
                'message': f'Successfully archived {archived_count} leave request(s). {failed_count} failed.',
                'data': {
                    'archived_count': archived_count,
                    'failed_count': failed_count,
                    'archived_ids': archived_ids
                }
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error during batch archiving: {str(e)}'
            }, status=400)


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.AllowAny]

    def destroy(self, request, *args, **kwargs):
        department = self.get_object()
        employee_count = department.employees.count()
        dean_count = Dean.objects.filter(department=department).count()
        
        if employee_count > 0:
            return Response({
                'success': False,
                'message': f'Cannot delete department. {employee_count} employee(s) are assigned to this department.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if dean_count > 0:
            return Response({
                'success': False,
                'message': f'Cannot delete department. {dean_count} dean(s) are assigned to this department.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        department.delete()
        return Response({
            'success': True,
            'message': 'Department deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def employees(self, request, pk=None):
        department = self.get_object()
        employees = department.employees.filter(is_active=True)
        serializer = EmployeeSerializer(employees, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def dean(self, request, pk=None):
        department = self.get_object()
        dean = Dean.objects.filter(department=department, is_active=True).first()
        if dean:
            serializer = DeanSerializer(dean, context={'request': request})
            return Response({'success': True, 'data': serializer.data})
        return Response({'success': False, 'message': 'No dean assigned to this department'})


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = [permissions.AllowAny]

    def destroy(self, request, *args, **kwargs):
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
        position = self.get_object()
        employees = position.employees.filter(is_active=True)
        serializer = EmployeeSerializer(employees, many=True, context={'request': request})
        return Response(serializer.data)

class IsDeanOrHR(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            request.user == obj.user or
            request.user.groups.filter(name='HR').exists()
        )

class DeanViewSet(viewsets.ModelViewSet):
    queryset = Dean.objects.all()
    serializer_class = DeanSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        dean = self.get_object()
        serializer = self.get_serializer(dean)
        return Response({'success': True, 'data': serializer.data})

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsDeanOrHR()]
        return [permissions.IsAuthenticated()]


    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        password = request.data.get('password')
        if password:
            instance.user.set_password(password)
            instance.user.save()

        username = request.data.get('username')
        if username and username != instance.user.username:
            if User.objects.filter(username=username).exclude(id=instance.user.id).exists():
                return Response({
                    'success': False,
                    'message': 'Username already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            instance.user.username = username
            instance.user.save()

        data = request.data.copy()
        data.pop('is_active', None)

        for field in ['username', 'password', 'department_name', 'department_code',
                    'photo_url', 'created_at', 'updated_at', 'is_dean']:
            data.pop(field, None)

        for num_field in ['age', 'height', 'weight']:
            if data.get(num_field) == '':
                data.pop(num_field)

        serializer = self.get_serializer(instance, data=data, partial=partial)

        if not serializer.is_valid():
            print(serializer.errors)
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        dean = serializer.save()
        dean.is_active = True
        dean.save()
        
        return Response({
            'success': True,
            'message': 'Dean updated successfully',
            'data': DeanSerializer(dean, context={'request': request}).data
        })

    def destroy(self, request, *args, **kwargs):
        dean = self.get_object()
        user = dean.user
        
        try:
            with transaction.atomic():
                dean.delete()
                user.delete()
                return Response({
                    'success': True,
                    'message': 'Dean account deleted successfully'
                }, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error deleting dean: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def by_department(self, request):
        department_id = request.query_params.get('department')
        if department_id:
            dean = Dean.objects.filter(department_id=department_id, is_active=True).first()
            if dean:
                serializer = self.get_serializer(dean)
                return Response({'success': True, 'data': serializer.data})
            return Response({'success': False, 'message': 'No dean found for this department'})
        return Response({'success': False, 'message': 'Department ID required'}, status=400)

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

    #def deactivate_employee(self, request, *args, **kwargs):
    #    employee = self.get_object()
    #    employee.is_active = False
    #    employee.save()
    #    return Response({
    #        'success': True,
    #        'message': 'Employee deactivated',
    #        'data': EmployeeSerializer(employee, context={'request': request}).data
    #    }, status=status.HTTP_200_OK)
        
    def destroy(self, request, *args, **kwargs):
        employee = self.get_object()
        employee.delete()
        return Response(
            {
                'success': True,
                'message': 'Employee permanently deleted'
            },
            status=status.HTTP_204_NO_CONTENT
        )

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
    queryset = LeaveApplication.objects.all()
    serializer_class = LeaveApplicationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        employee_id = request.data.get('employee')
        number_of_days = request.data.get('number_of_days')
        
        try:
            employee = Employee.objects.get(id=employee_id, is_active=True)
        except Employee.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Employee not found in records. Please verify your name.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        current_year = timezone.now().year
        try:
            balance = EmployeeLeaveBalance.objects.get(
                employee=employee,
                year=current_year
            )
        except EmployeeLeaveBalance.DoesNotExist:
            balance = EmployeeLeaveBalance.objects.create(
                employee=employee,
                year=current_year,
                remaining_days=15
            )
        
        try:
            days = int(number_of_days)
        except (ValueError, TypeError):
            return Response({
                'success': False,
                'message': 'Invalid number of days'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if days > 15:
            return Response({
                'success': False,
                'message': 'Maximum leave application is 15 days per request'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if days > balance.remaining_days:
            return Response({
                'success': False,
                'message': f'Insufficient leave balance. You only have {balance.remaining_days} days remaining for {current_year}.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            application = serializer.save()
            
            balance.deduct_days(days)
            
            LeaveRequest.objects.create(application=application, status='pending')
            
            return Response({
                'success': True,
                'message': f'Leave application submitted successfully! Pending dean approval. {balance.remaining_days} days remaining.',
                'data': serializer.data,
                'remaining_days': balance.remaining_days
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if instance.status != 'pending':
            return Response({
                'success': False,
                'message': f'Cannot update {instance.status} leave application'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        application = self.get_object()
        
        if application.status != 'pending':
            return Response({
                'success': False,
                'message': f'Cannot delete {application.status} leave application'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            current_year = timezone.now().year
            balance = EmployeeLeaveBalance.objects.get(
                employee=application.employee,
                year=current_year
            )
            balance.remaining_days += application.number_of_days
            balance.save()
        except EmployeeLeaveBalance.DoesNotExist:
            pass
        
        application.delete()
        return Response({
            'success': True,
            'message': 'Leave application deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)

class LeaveReportViewSet(viewsets.ModelViewSet):
    queryset = LeaveReport.objects.all()
    serializer_class = LeaveReportSerializer
    permission_classes = [permissions.IsAuthenticated, IsHROrDean]

    def get_queryset(self):
        user = self.request.user
        queryset = LeaveReport.objects.all()

        if hasattr(user, 'dean_profile'):
            dean = user.dean_profile
            queryset = queryset.filter(employee__department=dean.department).exclude(dean_status='pending')

        elif user.groups.filter(name='HR').exists():
            queryset = queryset.exclude(dean_status='pending')

        else:
            queryset = queryset

        return queryset

    @action(detail=False, methods=['get'])
    def recent(self, request):
        limit = int(request.query_params.get('limit', 10))
        reports = self.get_queryset()[:limit]
        serializer = self.get_serializer(reports, many=True)
        return Response({'success': True, 'data': serializer.data})

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        from django.db.models import Count
        queryset = self.get_queryset()
        stats = queryset.values('leave_type').annotate(count=Count('leave_type'))
        return Response({
            'success': True,
            'total_reports': queryset.count(),
            'by_leave_type': stats
        })

class HRUserViewSet(viewsets.ModelViewSet):
    queryset = HRUser.objects.all()
    serializer_class = HRUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'username'

    def get_object(self):
        username = self.kwargs.get(self.lookup_field)
        return HRUser.objects.get(user__username=username)


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
    total_employees = Employee.objects.filter(is_active=True).count()
    inactive_employees = Employee.objects.filter(is_active=False).count()
    pending_leaves = LeaveRequest.objects.filter(status='pending').count()
    approved_leaves = LeaveRequest.objects.filter(status='approved').count()
    denied_leaves = LeaveRequest.objects.filter(status='denied').count()
    
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

@csrf_exempt
@require_http_methods(["DELETE"])
@login_required
def delete_leave_request_if_denied(request, pk):
    user = request.user

    if not (hasattr(user, 'dean_profile') and getattr(user.dean_profile, 'is_dean', False)):
        return JsonResponse(
            {"error": "Only Dean accounts can delete this request."},
            status=403
        )

    try:
        leave_request = LeaveRequest.objects.get(pk=pk, status='dean_denied')
    except LeaveRequest.DoesNotExist:
        return JsonResponse(
            {"error": "Leave request not found or not eligible for deletion."},
            status=404
        )

    if hasattr(leave_request, "is_pending_hr") and leave_request.is_pending_hr:
        return JsonResponse(
            {"error": "Leave request is still pending HR, cannot delete."},
            status=400
        )

    leave_request.delete()
    return JsonResponse(
        {"success": f"Leave request {pk} deleted successfully."},
        status=200
    )


def appointment_form_view(request):
    return render(request, 'leave_requests_interface.html')

def starting_view(request):
    return render(request, "index.html")

@api_view(['PUT', 'PATCH'])
def update_department_name(request, pk):
    department = get_object_or_404(Department, pk=pk)
    new_name = request.data.get('name')

    if not new_name:
        return Response(
            {"success": False, "message": "Department name is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    department.name = new_name
    department.save()

    return Response(
        {
            "success": True,
            "message": "Department name updated successfully!",
            "data": {
                "id": department.id,
                "code": department.code,
                "name": department.name,
                "description": department.description,
            }
        },
        status=status.HTTP_200_OK
    )

def dean_dash_view(request):
    return render(request, "dean_dash.html")

@login_required
def HR_dash_view(request):
    return render(request, "Dashboard.html")

@csrf_exempt
def hr_login(request):
    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None and hasattr(user, 'hruser') and user.hruser.is_hr:
            login(request, user)
            return JsonResponse({
                "success": True,
                "message": "Login successful",
                "username": user.username,
                "full_name": user.hruser.full_name,
                "photo_url": user.hruser.photo.url if user.hruser.photo else None
            })
        else:
            return JsonResponse({"success": False, "message": "Invalid credentials"})

@csrf_exempt
def logout_view(request):
    if request.user.is_authenticated:
        logout(request)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({"success": True, "message": "Logged out successfully", "redirect_url": "/"})
    
    return redirect('/')

@ensure_csrf_cookie
def csrf(request):
    return JsonResponse({'detail': 'CSRF cookie set'})

@login_required
def org_chart_view(request):
    hrs = HRUser.objects.all()
    deans = Dean.objects.filter(is_active=True).order_by('full_name')

    context = {
        "hrs": hrs,
        "deans": deans,
    }
    return render(request, "Dashboard.html", context)

@login_required
def org_chart_api(request):
    hrs = HRUser.objects.filter(is_hr=True)
    deans = Dean.objects.filter(is_active=True).select_related("department")

    data = {
        "hrs": [
            {
                "id": hr.id,
                "full_name": hr.full_name,
                "photo": hr.photo.url if hr.photo else "/static/assets/media/examplePIC.jpg",
                "position": hr.position,
            }
            for hr in hrs
        ],
        "deans": [
            {
                "id": dean.id,
                "username": dean.user.username,
                "full_name": dean.full_name,
                "department": dean.department.name,
                "photo": dean.photo.url if dean.photo else "/static/assets/media/examplePIC.jpg",
                "position": dean.position,
                "gender": dean.gender,
                "age": dean.age,
                "height": dean.height,
                "weight": dean.weight
            }
            for dean in deans
        ]
    }

    return JsonResponse(data, safe=True)

def get_positions(request):
    positions = Position.objects.all().values("id", "code", "title", "description", "created_at")
    return JsonResponse(list(positions), safe=False)

@csrf_exempt
def update_position(request, id):
    if request.method in ["PUT", "PATCH"]:
        position = get_object_or_404(Position, id=id)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        position.code = data.get("code", position.code)
        position.title = data.get("title", position.title)
        position.description = data.get("description", position.description)
        position.save()

        serializer = PositionSerializer(position)
        return JsonResponse({
            "success": True,
            "message": "Position updated successfully!",
            "position": serializer.data
        }, status=200)

    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def delete_position(request, id):
    if request.method == "DELETE":
        position = get_object_or_404(Position, id=id)
        serializer = PositionSerializer(position)

        if serializer.data.get("occupied"):
            occupied_by = serializer.data.get("occupied_by")
            message = "Cannot delete position. It is currently occupied."
            return JsonResponse({"success": False, "message": message}, status=400)

        position.delete()
        return JsonResponse({"success": True, "message": "Position deleted successfully!"}, status=200)

    return JsonResponse({"error": "Invalid request method"}, status=400)

import json

@csrf_exempt
@login_required
def update_dean_department(request, dean_id):
    if request.method == "POST":
        dean = get_object_or_404(Dean, id=dean_id)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        department_id = data.get("department_id")
        if not department_id:
            return JsonResponse({"error": "Department ID is required"}, status=400)

        department = get_object_or_404(Department, id=department_id)
        dean.department = department
        dean.save()

        return JsonResponse({
            "message": f"{dean.full_name} reassigned to {department.name}",
            "dean_id": dean.id,
            "new_department": department.name
        })

    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
@login_required
def delete_dean(request, dean_id):
    if request.method == "POST":
        dean = get_object_or_404(Dean, id=dean_id)
        dean.delete()
        return JsonResponse({"message": "Dean deleted successfully"})
    
    return JsonResponse({"error": "Invalid request method"}, status=405)
