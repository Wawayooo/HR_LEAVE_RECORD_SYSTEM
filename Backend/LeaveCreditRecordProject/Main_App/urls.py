from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from .views_create_user import *
from .archive_views import *

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'positions', PositionViewSet, basename='position')
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'leave-applications', LeaveApplicationViewSet, basename='leaveapplication')
router.register(r'leave-requests', LeaveRequestViewSet, basename='leaverequest')
router.register(r'leave-reports', LeaveReportViewSet, basename='leavereport')
router.register(r'hruser', HRUserViewSet, basename='hruser')
router.register(r'deans', DeanViewSet, basename='dean')

router.register(r'leave-request-archives', LeaveRequestArchiveViewSet, basename='leave-request-archive')

urlpatterns = [
    path('', starting_view, name='starting_page'),
    
    path('homepage/', home_view, name='home_page'),
    
    path('api/leave-requests/<int:pk>/approve-test/', test_approve),
    
    path('access-key/<int:key_id>/update/', update_access_key, name='update_access_key'),

    path('hr_dashboard/', HR_dash_view, name='hr-dashboard'),
    path('appointment_form/', appointment_form_view, name='appointment-form'),
    
    path('api/departments/<int:pk>/update-name/', update_department_name, name='update-department-name'),
    
    path('api/create-dean/', create_dean, name='create_dean'),
    path('api/dean-login/', dean_login, name='dean-login'),
    path('dean_dashboard/', dean_dash_view, name='dean-dashboard'),
    
    path('api/deans/me/', dean_me, name='dean-me'),
    
    path('dean_dashboard_data/', dean_dashboard_data, name='dean_dashboard_data'),
    
    path('logout/', logout_view, name='logout'),
    path('dean_logout/', dean_logout_view, name='logout'),

    path("hr_login/", hr_login, name="hr_login"),
    path('api/verify-key/', verify_key, name='verify-key'),
    
    path('api/leave-requests/<int:pk>/delete-if-denied/', delete_leave_request_if_denied, name='delete_leave_request_if_denied'),

    path('api/dashboard-stats/', dashboard_stats, name='dashboard-stats'),
    
    path("api/org-chart/", org_chart_api, name="org_chart_api"),
    path("org-chart/", org_chart_view, name="org_chart"),

    path('leave-request-archives/<int:pk>/export-pdf/', export_archive_pdf_view, name='export-archive-pdf'),
    
    path("positions/", get_positions, name="get_positions"),
    path("positions/update/<int:id>/", update_position, name="update_position"),
    path("positions/delete/<int:id>/", delete_position, name="delete_position"),
    
    path("dean/<int:dean_id>/update/", update_dean_department, name="update_dean_department"),
    path("dean/<int:dean_id>/delete/", delete_dean, name="delete_dean"),

    path('csrf/', csrf, name='csrf'),
    
    path('api/', include(router.urls)),
]


