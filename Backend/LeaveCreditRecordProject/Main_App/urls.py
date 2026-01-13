from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from .views_create_user import *

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'positions', PositionViewSet, basename='position')
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'leave-applications', LeaveApplicationViewSet, basename='leaveapplication')
router.register(r'leave-requests', LeaveRequestViewSet, basename='leaverequest')
router.register(r'leave-reports', LeaveReportViewSet, basename='leavereport')
router.register(r'hruser', HRUserViewSet, basename='hruser')
router.register(r'dean', DeanViewSet, basename='dean')

urlpatterns = [
    path('', starting_view, name='starting_page'),
    path('hr_dashboard/', HR_dash_view, name='hr-dashboard'),
    path('appointment_form/', appointment_form_view, name='appointment-form'),
    
    path('api/create-dean/', create_dean, name='create_dean'),
    path('api/dean-login/', dean_login, name='dean-login'),
    path('dean_dashboard/', dean_dash_view, name='dean-dashboard'),
    
    path('api/deans/me/', dean_me, name='dean-me'),
    
    path('dean_dashboard_data/', dean_dashboard_data, name='dean_dashboard_data'),
    
    path('logout/', logout_view, name='logout'),
    path('dean_logout/', dean_logout_view, name='logout'),

    path("hr_login/", hr_login, name="hr_login"),
    path('api/verify-key/', verify_key, name='verify-key'),

    path('api/dashboard-stats/', dashboard_stats, name='dashboard-stats'),

    path('csrf/', csrf, name='csrf'),
    
    path('api/', include(router.urls)),
]
