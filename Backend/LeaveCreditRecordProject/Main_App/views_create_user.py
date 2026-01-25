# views.py
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db import transaction
import json

from django.contrib.auth import authenticate, login
from django.utils.decorators import method_decorator


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import DeanSerializer

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Dean, Employee, LeaveRequest, LeaveReport, Department
from .serializers import EmployeeSerializer, LeaveRequestSerializer, LeaveReportSerializer

from django.contrib.auth import logout

@csrf_exempt
def create_dean(request):
    if not request.user.is_authenticated or not hasattr(request.user, 'hruser'):
        return JsonResponse({'success': False, 'message': 'Unauthorized: HR only'}, status=403)

    if request.method != "POST":
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        full_name = data.get('full_name')
        department_id = data.get('department')

        if not all([username, password, full_name, department_id]):
            return JsonResponse({'success': False, 'message': 'All fields are required'}, status=400)

        try:
            department_id = int(department_id)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'message': 'Invalid department ID'}, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'message': 'Username already exists'}, status=400)

        try:
            department = Department.objects.get(id=department_id)
        except Department.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Department not found'}, status=404)

        with transaction.atomic():
            user = User.objects.create_user(username=username, password=password, is_active=True)
            
            dean = Dean.objects.create(
                user=user,
                full_name=full_name,
                department=department,
                is_dean=True
            )

        return JsonResponse({
            'success': True,
            'message': f'Dean {full_name} created successfully',
            'dean_id': dean.id
        }, status=201)

    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)

csrf_exempt
def dean_login(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request method"}, status=405)
    
    try:
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    if not username or not password:
        return JsonResponse({"success": False, "message": "Username and password are required"}, status=400)

    user = authenticate(username=username, password=password)
    if user is None:
        return JsonResponse({"success": False, "message": "Invalid username or password"}, status=401)

    try:
        dean_profile = user.dean_profile
    except Dean.DoesNotExist:
        return JsonResponse({"success": False, "message": "User is not a Dean"}, status=403)

    if not dean_profile.is_active:
        return JsonResponse({"success": False, "message": "Dean account is inactive"}, status=403)

    login(request, user)

    return JsonResponse({
        "success": True,
        "message": f"Welcome, {dean_profile.full_name}!"
    })

@csrf_exempt
def dean_logout_view(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=405)

    if request.user.is_authenticated:
        logout(request)

    return JsonResponse({
        "success": True,
        "message": "Logged out successfully",
        "redirect_url": "/"
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dean_me(request):
    user = request.user

    if not hasattr(user, 'dean_profile'):
        return Response({'success': False, 'message': 'You are not a Dean'}, status=403)

    dean = user.dean_profile
    serializer = DeanSerializer(dean, context={'request': request})
    return Response({'success': True, 'data': serializer.data})

@login_required
def dean_dashboard_data(request):
    user = request.user

    try:
        dean = Dean.objects.get(user=user, is_active=True)
    except Dean.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Dean profile not found'}, status=404)

    if not dean.department:
        return JsonResponse({
            'success': True,
            'data': {
                'dean': {
                    'full_name': dean.full_name,
                    'department_name': None,
                    'gender': dean.gender,
                    'age': dean.age,
                    'height': dean.height,
                    'weight': dean.weight,
                    'photo_url': request.build_absolute_uri(dean.photo.url) if dean.photo else None,
                },
                'faculty': [],
                'leave_requests': [],
                'leave_reports': []
            }
        })

    faculty_qs = Employee.objects.filter(department=dean.department, is_active=True)
    faculty_data = EmployeeSerializer(faculty_qs, many=True, context={'request': request}).data

    leave_requests_qs = LeaveRequest.objects.filter(
        application__employee__department=dean.department
    ).order_by('-created_at')
    leave_requests_data = LeaveRequestSerializer(leave_requests_qs, many=True, context={'request': request}).data

    leave_reports_qs = LeaveReport.objects.filter(
        employee__department=dean.department
    ).order_by('-created_at')
    leave_reports_data = LeaveReportSerializer(leave_reports_qs, many=True, context={'request': request}).data
    
    #print(f"Data: {faculty_data}, {leave_requests_data}, {leave_reports_data}")
    return JsonResponse({
        'success': True,
        'data': {
            'dean': {
                'full_name': dean.full_name,
                'department': dean.department.id,
                'department_name': dean.department.name,
                'gender': dean.gender,
                'age': dean.age,
                'height': dean.height,
                'weight': dean.weight,
                'photo_url': request.build_absolute_uri(dean.photo.url) if dean.photo else None
            },
            'faculty': faculty_data,
            'leave_requests': leave_requests_data,
            'leave_reports': leave_reports_data
        }
    })
