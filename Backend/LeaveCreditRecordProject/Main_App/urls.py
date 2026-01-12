from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'positions', PositionViewSet, basename='position')
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'leave-applications', LeaveApplicationViewSet, basename='leaveapplication')
router.register(r'leave-requests', LeaveRequestViewSet, basename='leaverequest')
router.register(r'leave-reports', LeaveReportViewSet, basename='leavereport')
router.register(r'hruser', HRUserViewSet, basename='hruser')

urlpatterns = [
    # Template Views
    path('', starting_view, name='starting_page'),
    path('hr_dashboard/', HR_dash_view, name='hr-dashboard'),
    path('appointment_form/', appointment_form_view, name='appointment-form'),

    # API Routes
    path('api/', include(router.urls)),

    # Authentication
    path("hr_login/", hr_login, name="hr_login"),
    path('api/verify-key/', verify_key, name='verify-key'),

    # Dashboard stats
    path('api/dashboard-stats/', dashboard_stats, name='dashboard-stats'),
    
    path('csrf/', csrf, name='csrf'),
]
