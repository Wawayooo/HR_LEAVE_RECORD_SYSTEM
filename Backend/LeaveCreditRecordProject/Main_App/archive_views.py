from rest_framework import viewsets, permissions
from django.http import HttpResponse
from .models import LeaveRequestArchive
from .serializers import LeaveRequestArchiveSerializer
from django.shortcuts import get_object_or_404

class LeaveRequestArchiveViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint to view archived leave requests.
    """
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

def export_archive_pdf_view(request, pk):
    archive = get_object_or_404(LeaveRequestArchive, pk=pk)
    #pdf_buffer = export_leave_request_archive_pdf(archive)
    pdf_buffer = export_osmena_leave_application_pdf(archive)

    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="leave_archive_{archive.id}.pdf"'
    return response


from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO


def export_osmena_leave_application_pdf(archive_obj):
    """
    Generate an APPLICATION FOR LEAVE PDF form following Osmeña Colleges format.
    The entire form fits on a single A4 page.
    
    Args:
        archive_obj: Object containing leave application data
    
    Returns:
        BytesIO buffer containing the generated PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontSize=13,
        textColor=colors.HexColor("#333333"),
        alignment=TA_CENTER,
        spaceAfter=1,
        fontName='Helvetica-Bold'
    )
    
    subheader_style = ParagraphStyle(
        'SubHeaderStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor("#555555"),
        alignment=TA_CENTER,
        spaceAfter=0
    )
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=12,
        textColor=colors.black,
        alignment=TA_CENTER,
        spaceAfter=6,
        spaceBefore=3,
        fontName='Helvetica-Bold'
    )
    
    section_header_style = ParagraphStyle(
        'SectionHeaderStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=3,
        spaceBefore=3
    )
    
    small_text = ParagraphStyle(
        'SmallText',
        parent=styles['Normal'],
        fontSize=7.5,
        leading=9
    )
    
    tiny_text = ParagraphStyle(
        'TinyText',
        parent=styles['Normal'],
        fontSize=7,
        leading=8
    )
    
    # Institution Header
    story.append(Paragraph("OSMEÑA COLLEGES", header_style))
    story.append(Paragraph("City of Masbate, 5400, Philippines", subheader_style))
    story.append(Paragraph("Tel: (056) 333-4444", subheader_style))
    story.append(Paragraph('E-Mail Address: <font color="blue">osmenocolleges@yahoo.com.ph</font>', subheader_style))
    story.append(Spacer(1, 3*mm))
    
    # Horizontal line
    line_table = Table([[""]], colWidths=[17*inch/2.54])
    line_table.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,0), 1.5, colors.black),
    ]))
    story.append(line_table)
    
    # Title with background
    title_data = [["APPLICATION FOR LEAVE"]]
    title_table = Table(title_data, colWidths=[17*inch/2.54])
    title_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.lightgrey),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 11),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(title_table)
    
    # Employee Information Section
    emp_info_data = [
        [Paragraph("<b>OSMEÑA COLLEGES</b>", tiny_text), "", "", ""],
        [Paragraph("<b>Office / Agency</b>", tiny_text), Paragraph("<b>Last Name</b>", tiny_text), 
         Paragraph("<b>First Name</b>", tiny_text), Paragraph("<b>Middle Name</b>", tiny_text)],
    ]
    
    emp_info_table = Table(emp_info_data, colWidths=[42*mm, 42*mm, 42*mm, 42*mm])
    emp_info_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(emp_info_table)
    
    # Parse employee name
    name_parts = archive_obj.employee_name.split() if hasattr(archive_obj, 'employee_name') else ["", "", ""]
    last_name = name_parts[-1] if len(name_parts) > 0 else ""
    first_name = name_parts[0] if len(name_parts) > 0 else ""
    middle_name = name_parts[1] if len(name_parts) > 2 else ""
    
    name_values_data = [["", last_name, first_name, middle_name]]
    name_values_table = Table(name_values_data, colWidths=[42*mm, 42*mm, 42*mm, 42*mm])
    name_values_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(name_values_table)
    
    # Department, Position, Date of Filing
    dept_position_data = [
        [Paragraph("<b>Department</b>", tiny_text), Paragraph("<b>Position</b>", tiny_text), 
         Paragraph("<b>Date of Filing</b>", tiny_text)],
    ]
    dept_position_table = Table(dept_position_data, colWidths=[56*mm, 56*mm, 56*mm])
    dept_position_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(dept_position_table)
    
    # Department values
    dept_values_data = [[
        archive_obj.employee_department if hasattr(archive_obj, 'employee_department') else "",
        archive_obj.employee_position if hasattr(archive_obj, 'employee_position') else "",
        archive_obj.date_filed.strftime("%B %d, %Y") if hasattr(archive_obj, 'date_filed') else ""
    ]]
    dept_values_table = Table(dept_values_data, colWidths=[56*mm, 56*mm, 56*mm])
    dept_values_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(dept_values_table)
    
    # DETAILS OF APPLICATION header
    details_header_data = [[Paragraph("<b>DETAILS OF APPLICATION</b>", section_header_style)]]
    details_header_table = Table(details_header_data, colWidths=[17*inch/2.54])
    details_header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.lightgrey),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(details_header_table)
    
    # Leave type checkboxes
    leave_type = archive_obj.get_leave_type_display() if hasattr(archive_obj, 'get_leave_type_display') else ""
    vacation_check = "☑" if "vacation" in leave_type.lower() else "☐"
    sick_check = "☑" if "sick" in leave_type.lower() else "☐"
    maternity_check = "☑" if "maternity" in leave_type.lower() else "☐"
    
    num_days = archive_obj.number_of_days if hasattr(archive_obj, 'number_of_days') else ""
    
    # Two-column layout for leave details
    left_column = f"""
<b>TYPE OF LEAVE</b><br/>
<br/>
[ ] Vacation<br/>
[ ] To seek employment<br/>
[ ] Others (specify)<br/>
<br/>
_________________________________<br/>
<br/>
<br/>
[ ] Sick<br/>
[ ] Maternity<br/>
[ ] Others (specify)<br/>
<br/>
_________________________________<br/>
<br/>
<br/>
No. of Working Days applied for: _____ <b>DAY</b><br/>
Inclusive Dates: ___________________________
    """
    
    right_column = f"""
<b>WHERE LEAVE WILL BE SPENT</b><br/>
<i>*In case of vacation leave</i><br/>
[ ] Within the Philippines<br/>
[ ] Abroad (specify)<br/>
<br/>
_________________________________<br/>
<br/>
<i>*In case of sick leave</i><br/>
[ ] In Hospital (specify)<br/>
<br/>
_________________________________<br/>
<br/>
[ ] Out Patient (specify)<br/>
<br/>
_________________________________<br/>
<br/>
_________________________________<br/>
<i>Signature of Applicant</i>
    """
    
    details_data = [[
        Paragraph(left_column, small_text),
        Paragraph(right_column, small_text)
    ]]
    
    details_table = Table(details_data, colWidths=[84*mm, 84*mm])
    details_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(details_table)
    
    # DETAILS OF ACTION ON APPLICATION header
    action_header_data = [[Paragraph("<b>DETAILS OF ACTION ON APPLICATION</b>", section_header_style)]]
    action_header_table = Table(action_header_data, colWidths=[17*inch/2.54])
    action_header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.lightgrey),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(action_header_table)
    
    # Leave credits section
    balance_before = archive_obj.leave_balance_before if hasattr(archive_obj, 'leave_balance_before') else "15"
    
    credits_and_rec = [
        [Paragraph("<b>TOTAL NO. OF LEAVE CREDITS:</b>", tiny_text), 
         Paragraph("<b>15 DAYS</b>", tiny_text), 
         Paragraph("<b>RECOMMENDATION:</b>", tiny_text)],
        [Paragraph("<b>LEAVE CREDITS AS OF:</b>", tiny_text), 
         "January 0, 1900", 
         "[ ]  Approval"],
        [Paragraph("<b>NO. OF LEAVE CREDITS:</b>", tiny_text), 
         "0", 
         "[ ]  Dissapproval due to"],
    ]
    
    credits_rec_table = Table(credits_and_rec, colWidths=[50*mm, 40*mm, 78*mm])
    credits_rec_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('ALIGN', (0,0), (1,-1), 'LEFT'),
        ('ALIGN', (2,0), (2,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(credits_rec_table)
    
    # Leave balance breakdown table
    balance_table_data = [
        [Paragraph("<b>Vacation/others</b>", tiny_text), 
         Paragraph("<b>Sick</b>", tiny_text), 
         Paragraph("<b>Total</b>", tiny_text), 
         Paragraph("<b>Remaining</b>", tiny_text),
         ""],
        ["", "", "", "15", ""],
        ["days", "days", "days", "days", ""],
    ]
    
    balance_table = Table(balance_table_data, colWidths=[30*mm, 30*mm, 30*mm, 30*mm, 48*mm])
    balance_table.setStyle(TableStyle([
        ('GRID', (0,0), (3,2), 0.5, colors.black),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(balance_table)
    
    # Bottom section with signatures
    hr_name = archive_obj.hr_reviewer_name if hasattr(archive_obj, 'hr_reviewer_name') else "JUNESSA CEZANNE REYES, RPm, CHRA"
    dean_name = archive_obj.dean_name if hasattr(archive_obj, 'dean_name') else "DR. FREDDIE T. BERNAL, CESO III"
    
    bottom_left = f"""
<br/>
<b>{hr_name}</b><br/>
<i>ACTING HR</i><br/>
<br/>
<i>Approved for:</i><br/>
<br/>
_____________ days with pay<br/>
_____________ days without pay<br/>
_____________ others (specify)
    """
    
    bottom_right = f"""
_________________________________<br/>
<i>Authorized Official</i><br/>
<br/>
<i>Recommending approval:</i><br/>
<br/>
<b>{dean_name}</b><br/>
<i>Vice President for Academic Affairs</i>
    """
    
    bottom_data = [[
        Paragraph(bottom_left, small_text),
        Paragraph(bottom_right, small_text)
    ]]
    
    bottom_table = Table(bottom_data, colWidths=[84*mm, 84*mm])
    bottom_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(bottom_table)
    
    story.append(Spacer(1, 3*mm))
    
    # President signature section
    president_data = [[
        Paragraph("<i>Approved by:</i>", small_text),
        Paragraph("<b>MIGUEL LUIS V. PELIÑO</b><br/><i>President</i>", 
                 ParagraphStyle('PresidentStyle', parent=small_text, alignment=TA_CENTER))
    ]]
    president_table = Table(president_data, colWidths=[84*mm, 84*mm])
    president_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(president_table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


# Example usage:
# buffer = export_osmena_leave_application_pdf(archive_obj)
# with open('leave_application.pdf', 'wb') as f:
#     f.write(buffer.read())

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO


def export_leave_request_archive_pdf(archive_obj):
    """
    Generate an APPLICATION FOR LEAVE PDF form following Osmeña Colleges format.
    
    Args:
        archive_obj: Object containing leave application data with attributes:
            - employee_name, employee_id, employee_department, employee_position
            - get_leave_type_display(), number_of_days, date_filed, reason
            - dean_name, dean_department, dean_reviewed_at, dean_comments
            - hr_reviewer_name, hr_reviewed_at, hr_comments
            - get_final_status_display(), leave_balance_before, leave_balance_after
            - archived_at, archived_by_system
    
    Returns:
        BytesIO buffer containing the generated PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor("#333333"),
        alignment=TA_CENTER,
        spaceAfter=2,
        fontName='Helvetica-Bold'
    )
    
    subheader_style = ParagraphStyle(
        'SubHeaderStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor("#555555"),
        alignment=TA_CENTER,
        spaceAfter=1
    )
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.black,
        alignment=TA_CENTER,
        spaceAfter=12,
        fontName='Helvetica-Bold',
        spaceBefore=6
    )
    
    section_header_style = ParagraphStyle(
        'SectionHeaderStyle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.black,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=6,
        spaceBefore=6
    )
    
    # Institution Header
    story.append(Paragraph("OSMEÑA COLLEGES", header_style))
    story.append(Paragraph("City of Masbate, 5400, Philippines", subheader_style))
    story.append(Paragraph("Tel: (056) 333-4444", subheader_style))
    story.append(Paragraph('E-Mail Address: <font color="blue">osmenocolleges@yahoo.com.ph</font>', subheader_style))
    story.append(Spacer(1, 8))
    
    # Horizontal line
    line_table = Table([[""]], colWidths=[7.5*inch])
    line_table.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,0), 2, colors.black),
    ]))
    story.append(line_table)
    
    # Title
    story.append(Paragraph("APPLICATION FOR LEAVE", title_style))
    
    # Employee Information Section
    emp_info_data = [
        ["OSMEÑA COLLEGES", "", "", ""],
        ["Office / Agency", "Last Name", "First Name", "Middle Name"],
    ]
    
    emp_info_table = Table(emp_info_data, colWidths=[1.9*inch, 1.9*inch, 1.9*inch, 1.9*inch])
    emp_info_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BACKGROUND', (0,1), (-1,1), colors.lightgrey),
    ]))
    story.append(emp_info_table)
    
    # Name values row
    name_parts = archive_obj.employee_name.split() if hasattr(archive_obj, 'employee_name') else ["", "", ""]
    last_name = name_parts[-1] if len(name_parts) > 0 else ""
    first_name = name_parts[0] if len(name_parts) > 0 else ""
    middle_name = name_parts[1] if len(name_parts) > 2 else ""
    
    name_values_data = [["", last_name, first_name, middle_name]]
    name_values_table = Table(name_values_data, colWidths=[1.9*inch, 1.9*inch, 1.9*inch, 1.9*inch])
    name_values_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(name_values_table)
    
    # Department, Position, Date of Filing
    dept_position_data = [
        ["Department", "Position", "Date of Filing"],
    ]
    dept_position_table = Table(dept_position_data, colWidths=[2.5*inch, 2.5*inch, 2.6*inch])
    dept_position_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
    ]))
    story.append(dept_position_table)
    
    # Department values
    dept_values_data = [[
        archive_obj.employee_department if hasattr(archive_obj, 'employee_department') else "",
        archive_obj.employee_position if hasattr(archive_obj, 'employee_position') else "",
        archive_obj.date_filed.strftime("%B %d, %Y") if hasattr(archive_obj, 'date_filed') else ""
    ]]
    dept_values_table = Table(dept_values_data, colWidths=[2.5*inch, 2.5*inch, 2.6*inch])
    dept_values_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(dept_values_table)
    
    story.append(Spacer(1, 4))
    story.append(Paragraph("DETAILS OF APPLICATION", section_header_style))
    
    # Leave type checkboxes
    leave_type = archive_obj.get_leave_type_display() if hasattr(archive_obj, 'get_leave_type_display') else ""
    vacation_check = "[X]" if "vacation" in leave_type.lower() else "[ ]"
    sick_check = "[X]" if "sick" in leave_type.lower() else "[ ]"
    maternity_check = "[X]" if "maternity" in leave_type.lower() else "[ ]"
    
    # Two-column layout for leave details
    left_column = f"""
    <b>TYPE OF LEAVE</b><br/>
    <br/>
    {vacation_check} Vacation<br/>
    [ ] To seek employment<br/>
    [ ] Others (specify)<br/>
    <br/>
    _________________________________<br/>
    <br/>
    <br/>
    {sick_check} Sick<br/>
    {maternity_check} Maternity<br/>
    [ ] Others (specify)<br/>
    <br/>
    _________________________________<br/>
    <br/>
    <br/>
    No. of Working Days applied for: <b>{archive_obj.number_of_days if hasattr(archive_obj, 'number_of_days') else '____'}</b> DAY<br/>
    Inclusive Dates: ___________________________
    """
    
    right_column = f"""
    <b>WHERE LEAVE WILL BE SPENT</b><br/>
    <i>*In case of vacation leave</i><br/>
    [ ] Within the Philippines<br/>
    [ ] Abroad (specify)<br/>
    <br/>
    _________________________________<br/>
    <br/>
    <i>*In case of sick leave</i><br/>
    [ ] In Hospital (specify)<br/>
    <br/>
    _________________________________<br/>
    <br/>
    [ ] Out Patient (specify)<br/>
    <br/>
    _________________________________<br/>
    <br/>
    _________________________________<br/>
    <i>Signature of Applicant</i>
    """
    
    details_data = [[
        Paragraph(left_column, styles['Normal']),
        Paragraph(right_column, styles['Normal'])
    ]]
    
    details_table = Table(details_data, colWidths=[3.8*inch, 3.8*inch])
    details_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(details_table)
    
    story.append(Spacer(1, 4))
    story.append(Paragraph("DETAILS OF ACTION ON APPLICATION", section_header_style))
    
    # Leave credits section
    balance_before = archive_obj.leave_balance_before if hasattr(archive_obj, 'leave_balance_before') else "15"
    balance_after = archive_obj.leave_balance_after if hasattr(archive_obj, 'leave_balance_after') and archive_obj.leave_balance_after is not None else balance_before
    
    credits_data = [
        ["TOTAL NO. OF LEAVE CREDITS:", "15 DAYS", "RECOMMENDATION:"],
        ["LEAVE CREDITS AS OF:", "January 0, 1900", "[ ] Approval"],
        ["NO. OF LEAVE CREDITS:", "0", "[ ] Dissapproval due to"],
    ]
    
    credits_table = Table(credits_data, colWidths=[2.5*inch, 2.0*inch, 3.1*inch])
    credits_table.setStyle(TableStyle([
        ('GRID', (0,0), (1,2), 1, colors.black),
        ('GRID', (2,0), (2,2), 1, colors.black),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ALIGN', (0,0), (1,-1), 'LEFT'),
        ('ALIGN', (2,0), (2,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,0), (0,0), colors.lightgrey),
        ('BACKGROUND', (0,1), (0,1), colors.lightgrey),
        ('BACKGROUND', (0,2), (0,2), colors.lightgrey),
        ('BACKGROUND', (2,0), (2,0), colors.lightgrey),
    ]))
    story.append(credits_table)
    
    # Leave balance table
    balance_table_data = [
        ["Vacation/others", "Sick", "Total", "Remaining"],
        ["", "", "", "15"],
        ["days", "days", "days", "days"],
    ]
    
    balance_table = Table(balance_table_data, colWidths=[1.4*inch, 1.1*inch, 1.1*inch, 1.0*inch])
    balance_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(balance_table)
    
    # Recommendation line
    rec_line_data = [["_________________________________"]]
    rec_line_table = Table(rec_line_data, colWidths=[3.1*inch])
    rec_line_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    
    # Bottom section with HR and VP signatures
    hr_name = archive_obj.hr_reviewer_name if hasattr(archive_obj, 'hr_reviewer_name') else "JUNESSA CEZANNE REYES, RPm, CHRA"
    dean_name = archive_obj.dean_name if hasattr(archive_obj, 'dean_name') else "DR. FREDDIE T. BERNAL, CESO III"
    
    bottom_left = f"""
    <br/>
    <b>{hr_name}</b><br/>
    <i>ACTING HR</i><br/>
    <br/>
    <i>Approved for:</i><br/>
    <br/>
    _____________ days with pay<br/>
    _____________ days without pay<br/>
    _____________ others (specify)
    """
    
    bottom_right = f"""
    _________________________________<br/>
    <i>Authorized Official</i><br/>
    <br/>
    <i>Recommending approval:</i><br/>
    <br/>
    <b>{dean_name}</b><br/>
    <i>Vice President for Academic Affairs</i>
    """
    
    bottom_data = [[
        Paragraph(bottom_left, styles['Normal']),
        Paragraph(bottom_right, styles['Normal'])
    ]]
    
    bottom_table = Table(bottom_data, colWidths=[3.8*inch, 3.8*inch])
    bottom_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(bottom_table)
    
    story.append(Spacer(1, 12))
    
    # President signature
    president_data = [[
        Paragraph("<i>Approved by:</i>", styles['Normal']),
        ""
    ]]
    president_table = Table(president_data, colWidths=[3.8*inch, 3.8*inch])
    story.append(president_table)
    
    story.append(Spacer(1, 8))
    
    president_sig_data = [[
        "",
        Paragraph("<b>MIGUEL LUIS V. PELIÑO</b><br/><i>President</i>", ParagraphStyle('Center', parent=styles['Normal'], alignment=TA_CENTER))
    ]]
    president_sig_table = Table(president_sig_data, colWidths=[3.8*inch, 3.8*inch])
    story.append(president_sig_table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer