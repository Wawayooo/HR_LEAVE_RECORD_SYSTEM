from rest_framework import viewsets, permissions
from django.http import HttpResponse
from .models import LeaveRequestArchive
from .serializers import LeaveRequestArchiveSerializer
from django.shortcuts import get_object_or_404

from .export_views import export_osmena_leave_application_pdf_non_teaching_format, export_osmena_leave_application_pdf_teaching_format

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, permissions

class LeaveRequestArchiveViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LeaveRequestArchive.objects.all()
    serializer_class = LeaveRequestArchiveSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = LeaveRequestArchive.objects.all()

        if hasattr(user, 'dean_profile'):
            qs = qs.filter(employee_department=user.dean_profile.department.name)
        elif hasattr(user, 'hruser') or user.groups.filter(name='HR').exists():
            qs = qs

        return qs
    
    def get_employee_archives(self, employee_id):
        user = self.request.user
        qs = LeaveRequestArchive.objects.all()

        if hasattr(user, 'dean_profile'):
            qs = qs.filter(employee_department=user.dean_profile.department.name)
        elif hasattr(user, 'hruser') or user.groups.filter(name='HR').exists():
            qs = qs

        if employee_id:
            qs = qs.filter(employee_id=employee_id)

        return qs

    @action(detail=False, methods=['get'], url_path='by-employee/(?P<employee_id>[^/.]+)')
    def by_employee(self, request, employee_id=None):
        qs = self.get_employee_archives(employee_id)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


    @action(detail=True, methods=['delete'], url_path='delete', permission_classes=[permissions.IsAuthenticated])
    def delete_archive(self, request, pk=None):
        user = request.user

        if not (hasattr(user, 'hruser') or user.groups.filter(name='HR').exists()):
            return Response({'success': False, 'message': 'Only HR can delete archives.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            archive = self.get_object()
            archive.delete()
            return Response({'success': True, 'message': 'Archive deleted permanently.'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'success': False, 'message': f'Error deleting archive: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

def export_archive_pdf_view(request, pk):
    archive = get_object_or_404(LeaveRequestArchive, pk=pk)
    position = (archive.employee_position or "").lower()

    teaching_keywords = ["instructor", "teacher", "educator", "coach"]

    if any(keyword in position for keyword in teaching_keywords):
        pdf_buffer = export_osmena_leave_application_pdf_teaching_format(archive)
    else:
        pdf_buffer = export_osmena_leave_application_pdf_non_teaching_format(archive)

    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="leave_archive_{archive.id}.pdf"'
    return response
