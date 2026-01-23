from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from datetime import datetime


def export_osmena_leave_application_pdf_non_teaching_format(archive_obj):
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=12*mm,
        leftMargin=12*mm,
        topMargin=10*mm,
        bottomMargin=10*mm
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor("#333333"),
        alignment=TA_CENTER,
        spaceAfter=0.5*mm,
        fontName='Helvetica-Bold'
    )
    
    subheader_style = ParagraphStyle(
        'SubHeaderStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor("#555555"),
        alignment=TA_CENTER,
        spaceAfter=0
    )
    
    section_header_style = ParagraphStyle(
        'SectionHeaderStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.black,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=2*mm,
        spaceBefore=2*mm
    )
    
    small_text = ParagraphStyle(
        'SmallText',
        parent=styles['Normal'],
        fontSize=7,
        leading=8.5
    )
    
    tiny_text = ParagraphStyle(
        'TinyText',
        parent=styles['Normal'],
        fontSize=6.5,
        leading=7.5,
    )
    
    tiny_text2 = ParagraphStyle(
        'TinyText',
        parent=styles['Normal'],
        fontSize=6.5,
        leading=7.5,
        alignment=TA_CENTER
    )
    
    centered_name_style = ParagraphStyle(
        'CenteredName',
        parent=small_text,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    centered_title_style = ParagraphStyle(
        'CenteredTitle',
        parent=small_text,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique',
        fontSize=6.5
    )
    
    centered_line_style = ParagraphStyle(
        'CenteredLine',
        parent=small_text,
        alignment=TA_CENTER
    )
    
    centered_line_style2 = ParagraphStyle(
        'CenteredLine',
        parent=small_text,
        alignment=TA_LEFT,
        leftIndent=16*mm
    )
    
    small_text_2 = ParagraphStyle(
        'SmallText',
        alignment=TA_LEFT,
        parent=styles['Normal'],
        fontSize=7,
        leading=8.5,
        leftIndent=10*mm
    )
    
    centered_approved_style = ParagraphStyle(
        'CenteredApproved',
        parent=small_text,
        alignment=TA_CENTER,
        rightIndent=5*mm
    )
    
    def safe_get_attr(obj, attr_name, default=""):
        if hasattr(obj, attr_name):
            value = getattr(obj, attr_name)
            return value if value is not None else default
        return default
    
    def truncate_text(text, max_length=50):
        text_str = str(text) if text else ""
        if len(text_str) > max_length:
            return text_str[:max_length-3] + "..."
        return text_str
    
    employee_name = safe_get_attr(archive_obj, 'employee_name', '')
    employee_department = truncate_text(safe_get_attr(archive_obj, 'employee_department'), 30)
    employee_position = truncate_text(safe_get_attr(archive_obj, 'employee_position'), 30)

    date_filed = safe_get_attr(archive_obj, 'date_filed')
    if hasattr(date_filed, 'strftime'):
        date_filed_str = date_filed.strftime("%B %d, %Y")
    else:
        date_filed_str = str(date_filed) if date_filed else ""
    
    leave_type = str(safe_get_attr(archive_obj, 'leave_type', '')).lower()
    number_of_days = str(safe_get_attr(archive_obj, 'number_of_days', ''))
    leave_balance_after = safe_get_attr(archive_obj, 'leave_balance_after', '15')
    
    vacation_location = str(safe_get_attr(archive_obj, 'vacation_location', '')).lower()
    sick_location = str(safe_get_attr(archive_obj, 'sick_location', '')).lower()
    reason = safe_get_attr(archive_obj, 'reason', '')
    
    vacation_check = '[✔]' if leave_type == 'vacation' else '[ ]'
    sick_check = '[✔]' if leave_type == 'sick' else '[ ]'
    maternity_check = '[✔]' if leave_type in ['maternity', 'paternity'] else '[ ]'
    
    philippines_check = '[ ]'
    abroad_check = '[ ]'
    abroad_reason = '_________________________'
    
    if leave_type == 'vacation':
        if vacation_location == 'philippines':
            philippines_check = '[✔]'
        elif vacation_location == 'abroad':
            abroad_check = '[✔]'
            abroad_reason = f'<u>{reason}</u>' if reason else '_________________________'
    
    hospital_check = '[ ]'
    home_check = '[ ]'
    hospital_reason = '_________________________'
    
    if leave_type == 'sick':
        if sick_location == 'hospital':
            hospital_check = '[✔]'
            hospital_reason = f'<u>{reason}</u>' if reason else '_________________________'
        elif sick_location == 'home':
            home_check = '[✔]'
    
    others_check = '[ ]'
    others_reason = '_________________________'
    if leave_type == 'emergency':
        others_check = '[✔]'
        others_reason = f'<u>Emergency Leave: {reason}</u>' if reason else '_________________________'

    logo = Image(r"C:\Users\buddy\OneDrive\Desktop\HR_LeaveManagement\Backend\LeaveCreditRecordProject\Main_App\oc_logo.png")
    logo.drawHeight = 15*mm
    logo.drawWidth = 15*mm

    info_block = [
        Paragraph("OSMEÑA COLLEGES", header_style),
        Paragraph("City of Masbate, 5400, Philippines", subheader_style),
        Paragraph("Tel: (056) 333-4444", subheader_style),
        Paragraph('E-Mail: <font color="blue">osmenacolleges@yahoo.com.ph</font>', subheader_style),
    ]

    info_table = Table([[info_block]], colWidths=[186*mm])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))

    logo_table = Table([[logo]], colWidths=[186*mm])
    logo_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),    
        ('LEFTPADDING', (0,0), (0,0), 86*mm), 
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('MARGINTOP', (0,0), (-1,-1), 0*mm),
    ]))

    story.append(logo_table)
    story.append(info_table)
    story.append(Spacer(1, 2*mm))

    line_table = Table([[""]], colWidths=[186*mm])
    line_table.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,0), 1.5, colors.black),
    ]))
    story.append(line_table)


    line_table = Table([[""]], colWidths=[186*mm])
    line_table.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,0), 1.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(line_table)
        
    title_data = [["APPLICATION FOR LEAVE"]]
    title_table = Table(title_data, colWidths=[186*mm])
    title_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.lightgrey),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(title_table)
    
    emp_header_data = [
        [Paragraph("<b>Office / Agency</b>", tiny_text), Paragraph("<b>Full Name</b>", tiny_text)],
        [Paragraph("OSMEÑA COLLEGES", tiny_text2), Paragraph(employee_name, tiny_text2)],
    ]

    emp_header_table = Table(emp_header_data, colWidths=[93*mm, 93*mm])
    emp_header_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(emp_header_table)
    
    dept_header_data = [
        [Paragraph("<b>Department</b>", tiny_text), 
         Paragraph("<b>Position</b>", tiny_text), 
         Paragraph("<b>Date of Filing</b>", tiny_text)],
    ]
    dept_header_table = Table(dept_header_data, colWidths=[62*mm, 62*mm, 62*mm])
    dept_header_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(dept_header_table)
    
    dept_values_data = [[employee_department, employee_position, date_filed_str]]
    dept_values_table = Table(dept_values_data, colWidths=[62*mm, 62*mm, 62*mm])
    dept_values_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(dept_values_table)
    
    details_header_data = [[Paragraph("<b>DETAILS OF APPLICATION</b>", section_header_style)]]
    details_header_table = Table(details_header_data, colWidths=[186*mm])
    details_header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.lightgrey),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(details_header_table)
    
    left_column = f"""
        <b>TYPE OF LEAVE</b><br/>
        <br/>
        {vacation_check} Vacation<br/>
        [ ] To seek employment<br/>
        {others_check} Others (specify)<br/>
        <br/>
                {others_reason}<br/>
        <br/>
        <br/>
        {sick_check} Sick<br/>
        {maternity_check} Maternity/Paternity<br/>
        <br/>
        <br/>
        No. of Working Days: <b>{number_of_days} Day/s</b><br/>
        <br/>
        <br/>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Inclusive Dates: ________ / ________
    """
    
    right_column = f"""
        <b>WHERE LEAVE WILL BE SPENT</b><br/>
        <i>*In case of vacation leave</i><br/>
        {philippines_check} Within the Philippines<br/>
        {abroad_check} Abroad (specify)<br/>
        <br/>
                {abroad_reason}<br/>
        <br/>
        <i>*In case of sick leave</i><br/>
        {hospital_check} In Hospital (specify)<br/>
        <br/>
                {hospital_reason}<br/>
        <br/>
        {home_check} Out Patient (specify)<br/>
        <br/>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;______________________________________________________
        <br/>
        <br/>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_____________________________<br/>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Signature of Applicant</i>
    """
    
    details_data = [[
        Paragraph(left_column, small_text),
        Paragraph(right_column, small_text)
    ]]
    
    details_table = Table(details_data, colWidths=[93*mm, 93*mm])
    details_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(details_table)
    
    action_header_data = [[Paragraph("<b>DETAILS OF ACTION ON APPLICATION</b>", 
                                    section_header_style)]]
    action_header_table = Table(action_header_data, colWidths=[186*mm])
    action_header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.lightgrey),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(action_header_table)
    
    current_date = datetime.now().strftime("%B %d, %Y")
    
    summary_data = [
        [Paragraph("<b>TOTAL NO. OF LEAVE CREDITS:</b>", tiny_text), 
         Paragraph(f"<b>{number_of_days}-DAY</b>", tiny_text), 
         ""],
        [Paragraph("<b>LEAVE CREDITS AS OF:</b>", tiny_text), 
         current_date, 
         ""],
        [Paragraph("<b>NO. OF LEAVE CREDITS:</b>", tiny_text), 
         f"{leave_balance_after}-DAY", 
         ""]
    ]
    summary_table = Table(summary_data, colWidths=[55*mm, 45*mm, 86*mm])
    summary_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('ALIGN', (0,0), (1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(summary_table)
    
    vacation_days = "0"
    sick_days = "0"
    
    if leave_type in ['vacation', 'paternity', 'maternity', 'emergency']:
        vacation_days = str(number_of_days)
    elif leave_type == 'sick':
        sick_days = str(number_of_days)
    
    credits_header = [
        [Paragraph("<b>Vacation/others</b>", small_text),
         Paragraph("<b>Sick</b>", small_text),
         Paragraph("<b>Total</b>", small_text),
         Paragraph("<b>Remaining</b>", small_text)]
    ]
    
    credits_values = [
        [Paragraph(f"{vacation_days} days", small_text),
         Paragraph(f"{sick_days} days", small_text),
         Paragraph(f"{number_of_days} days", small_text),
         Paragraph(f"{leave_balance_after} days", small_text)]
    ]
    
    credits_table = Table(credits_header + credits_values, 
                         colWidths=[23*mm, 19*mm, 19*mm, 18.3*mm])
    credits_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    
    left_side_elements = [
        credits_table,
        Spacer(1, 2*mm),
        Paragraph("<i>Personnel Officer:</i>", small_text),
        Spacer(1, 2*mm),
        Paragraph("<u><b>JUNESSA CEZANNE REYES, RPm, CHRA</b></u>", centered_name_style),
        Paragraph("ACTING HR", centered_title_style),
        Spacer(1, 2*mm),
        Paragraph("<i>Approved for:</i>", small_text),
        Paragraph("_______ days with pay", centered_approved_style),
        Paragraph("_______ days without pay", centered_approved_style),
        Paragraph("_______ others (specify)", centered_approved_style)
    ]
    
    right_side_elements = [
        Paragraph("<b>RECOMMENDATION:</b>", small_text),
        Paragraph("[ ] Approval<br/>[ ] Disapproval due to", small_text_2),
        Spacer(1, 1*mm),
        Paragraph("__________________________________________________", centered_line_style2),
        Spacer(1, 6*mm),
        Paragraph("_________________________", centered_line_style),
        Spacer(1, 1*mm),
        Paragraph("<i>Authorized Official</i>", centered_title_style),
        Spacer(1, 4*mm),
        Paragraph("<i>Recommending approval:</i>", small_text),
        Spacer(1, 2*mm),
        Paragraph("<u><b>LORENZO GABRIEL V. PELIÑO</b></u>", centered_name_style),
        Paragraph("<i>Vice President for Administration and Finance</i>", centered_title_style)
    ]
    
    main_content_data = [[left_side_elements, right_side_elements]]
    main_content_table = Table(main_content_data, colWidths=[82*mm, 104*mm])
    main_content_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(main_content_table)
    
    story.append(Spacer(1, 3*mm))
    
    president_left_style = ParagraphStyle(
        'PresidentLeft',
        parent=small_text,
        alignment=TA_LEFT,
        leftIndent=45*mm,
    )
    
    story.append(Paragraph("<i>Approved by:</i>", president_left_style))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("<u><b>MIGUEL LUIS V. PELIÑO</b></u>", centered_name_style))
    story.append(Paragraph("<i>President</i>", centered_title_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def export_osmena_leave_application_pdf_teaching_format(archive_obj):
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=12*mm,
        leftMargin=12*mm,
        topMargin=10*mm,
        bottomMargin=10*mm
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor("#333333"),
        alignment=TA_CENTER,
        spaceAfter=0.5*mm,
        fontName='Helvetica-Bold'
    )
    
    subheader_style = ParagraphStyle(
        'SubHeaderStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor("#555555"),
        alignment=TA_CENTER,
        spaceAfter=0
    )
    
    section_header_style = ParagraphStyle(
        'SectionHeaderStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.black,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=2*mm,
        spaceBefore=2*mm
    )
    
    small_text = ParagraphStyle(
        'SmallText',
        parent=styles['Normal'],
        fontSize=7,
        leading=8.5
    )
    
    tiny_text = ParagraphStyle(
        'TinyText',
        parent=styles['Normal'],
        fontSize=6.5,
        leading=7.5,
    )
    
    tiny_text2 = ParagraphStyle(
        'TinyText',
        parent=styles['Normal'],
        fontSize=6.5,
        leading=7.5,
        alignment=TA_CENTER
    )
    
    centered_name_style = ParagraphStyle(
        'CenteredName',
        parent=small_text,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    centered_title_style = ParagraphStyle(
        'CenteredTitle',
        parent=small_text,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique',
        fontSize=6.5
    )
    
    centered_line_style = ParagraphStyle(
        'CenteredLine',
        parent=small_text,
        alignment=TA_CENTER
    )
    
    centered_line_style2 = ParagraphStyle(
        'CenteredLine',
        parent=small_text,
        alignment=TA_LEFT,
        leftIndent=16*mm
    )
    
    small_text_2 = ParagraphStyle(
        'SmallText',
        alignment=TA_LEFT,
        parent=styles['Normal'],
        fontSize=7,
        leading=8.5,
        leftIndent=10*mm
    )
    
    centered_approved_style = ParagraphStyle(
        'CenteredApproved',
        parent=small_text,
        alignment=TA_CENTER,
        rightIndent=5*mm
    )
    
    def safe_get_attr(obj, attr_name, default=""):
        if hasattr(obj, attr_name):
            value = getattr(obj, attr_name)
            return value if value is not None else default
        return default
    
    def truncate_text(text, max_length=50):
        text_str = str(text) if text else ""
        if len(text_str) > max_length:
            return text_str[:max_length-3] + "..."
        return text_str
    
    employee_name = safe_get_attr(archive_obj, 'employee_name', '')
    employee_department = truncate_text(safe_get_attr(archive_obj, 'employee_department'), 30)
    employee_position = truncate_text(safe_get_attr(archive_obj, 'employee_position'), 30)

    date_filed = safe_get_attr(archive_obj, 'date_filed')
    if hasattr(date_filed, 'strftime'):
        date_filed_str = date_filed.strftime("%B %d, %Y")
    else:
        date_filed_str = str(date_filed) if date_filed else ""
    
    leave_type = str(safe_get_attr(archive_obj, 'leave_type', '')).lower()
    number_of_days = str(safe_get_attr(archive_obj, 'number_of_days', ''))
    leave_balance_after = safe_get_attr(archive_obj, 'leave_balance_after', '15')
    
    vacation_location = str(safe_get_attr(archive_obj, 'vacation_location', '')).lower()
    sick_location = str(safe_get_attr(archive_obj, 'sick_location', '')).lower()
    reason = safe_get_attr(archive_obj, 'reason', '')
    
    vacation_check = '[✔]' if leave_type == 'vacation' else '[ ]'
    sick_check = '[✔]' if leave_type == 'sick' else '[ ]'
    maternity_check = '[✔]' if leave_type in ['maternity', 'paternity'] else '[ ]'
    
    philippines_check = '[ ]'
    abroad_check = '[ ]'
    abroad_reason = '_________________________'
    
    if leave_type == 'vacation':
        if vacation_location == 'philippines':
            philippines_check = '[✔]'
        elif vacation_location == 'abroad':
            abroad_check = '[✔]'
            abroad_reason = f'<u>{reason}</u>' if reason else '_________________________'
    
    hospital_check = '[ ]'
    home_check = '[ ]'
    hospital_reason = '_________________________'
    
    if leave_type == 'sick':
        if sick_location == 'hospital':
            hospital_check = '[✔]'
            hospital_reason = f'<u>{reason}</u>' if reason else '_________________________'
        elif sick_location == 'home':
            home_check = '[✔]'
    
    others_check = '[ ]'
    others_reason = '_________________________'
    if leave_type == 'emergency':
        others_check = '[✔]'
        others_reason = f'<u>Emergency Leave: {reason}</u>' if reason else '_________________________'

    logo = Image(r"C:\Users\buddy\OneDrive\Desktop\HR_LeaveManagement\Backend\LeaveCreditRecordProject\Main_App\oc_logo.png")
    logo.drawHeight = 15*mm
    logo.drawWidth = 15*mm

    info_block = [
        Paragraph("OSMEÑA COLLEGES", header_style),
        Paragraph("City of Masbate, 5400, Philippines", subheader_style),
        Paragraph("Tel: (056) 333-4444", subheader_style),
        Paragraph('E-Mail: <font color="blue">osmenacolleges@yahoo.com.ph</font>', subheader_style),
    ]

    info_table = Table([[info_block]], colWidths=[186*mm])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))

    logo_table = Table([[logo]], colWidths=[186*mm])
    logo_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),    
        ('LEFTPADDING', (0,0), (0,0), 86*mm), 
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('MARGINTOP', (0,0), (-1,-1), 0*mm),
    ]))

    story.append(logo_table)
    story.append(info_table)
    story.append(Spacer(1, 2*mm))

    line_table = Table([[""]], colWidths=[186*mm])
    line_table.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,0), 1.5, colors.black),
    ]))
    story.append(line_table)


    line_table = Table([[""]], colWidths=[186*mm])
    line_table.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,0), 1.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(line_table)
        
    title_data = [["APPLICATION FOR LEAVE"]]
    title_table = Table(title_data, colWidths=[186*mm])
    title_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.lightgrey),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(title_table)
    
    emp_header_data = [
        [Paragraph("<b>Office / Agency</b>", tiny_text), Paragraph("<b>Full Name</b>", tiny_text)],
        [Paragraph("OSMEÑA COLLEGES", tiny_text2), Paragraph(employee_name, tiny_text2)],
    ]

    emp_header_table = Table(emp_header_data, colWidths=[93*mm, 93*mm])
    emp_header_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(emp_header_table)
    
    dept_header_data = [
        [Paragraph("<b>Department</b>", tiny_text), 
         Paragraph("<b>Position</b>", tiny_text), 
         Paragraph("<b>Date of Filing</b>", tiny_text)],
    ]
    dept_header_table = Table(dept_header_data, colWidths=[62*mm, 62*mm, 62*mm])
    dept_header_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(dept_header_table)
    
    dept_values_data = [[employee_department, employee_position, date_filed_str]]
    dept_values_table = Table(dept_values_data, colWidths=[62*mm, 62*mm, 62*mm])
    dept_values_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(dept_values_table)
    
    details_header_data = [[Paragraph("<b>DETAILS OF APPLICATION</b>", section_header_style)]]
    details_header_table = Table(details_header_data, colWidths=[186*mm])
    details_header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.lightgrey),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(details_header_table)
    
    left_column = f"""
        <b>TYPE OF LEAVE</b><br/>
        <br/>
        {vacation_check} Vacation<br/>
        [ ] To seek employment<br/>
        {others_check} Others (specify)<br/>
        <br/>
                {others_reason}<br/>
        <br/>
        <br/>
        {sick_check} Sick<br/>
        {maternity_check} Maternity/Paternity<br/>
        <br/>
        <br/>
        No. of Working Days: <b>{number_of_days} Day/s</b><br/>
        <br/>
        <br/>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Inclusive Dates: ________ / ________
    """
    
    right_column = f"""
        <b>WHERE LEAVE WILL BE SPENT</b><br/>
        <i>*In case of vacation leave</i><br/>
        {philippines_check} Within the Philippines<br/>
        {abroad_check} Abroad (specify)<br/>
        <br/>
                {abroad_reason}<br/>
        <br/>
        <i>*In case of sick leave</i><br/>
        {hospital_check} In Hospital (specify)<br/>
        <br/>
                {hospital_reason}<br/>
        <br/>
        {home_check} Out Patient (specify)<br/>
        <br/>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;______________________________________________________
        <br/>
        <br/>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_____________________________<br/>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Signature of Applicant</i>
    """
    
    details_data = [[
        Paragraph(left_column, small_text),
        Paragraph(right_column, small_text)
    ]]
    
    details_table = Table(details_data, colWidths=[93*mm, 93*mm])
    details_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(details_table)
    
    action_header_data = [[Paragraph("<b>DETAILS OF ACTION ON APPLICATION</b>", 
                                    section_header_style)]]
    action_header_table = Table(action_header_data, colWidths=[186*mm])
    action_header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.lightgrey),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(action_header_table)
    
    current_date = datetime.now().strftime("%B %d, %Y")
    
    summary_data = [
        [Paragraph("<b>TOTAL NO. OF LEAVE CREDITS:</b>", tiny_text), 
         Paragraph(f"<b>{number_of_days}-DAY</b>", tiny_text), 
         ""],
        [Paragraph("<b>LEAVE CREDITS AS OF:</b>", tiny_text), 
         current_date, 
         ""],
        [Paragraph("<b>NO. OF LEAVE CREDITS:</b>", tiny_text), 
         f"{leave_balance_after}-DAY", 
         ""]
    ]
    summary_table = Table(summary_data, colWidths=[55*mm, 45*mm, 86*mm])
    summary_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('ALIGN', (0,0), (1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(summary_table)
    
    vacation_days = "0"
    sick_days = "0"
    
    if leave_type in ['vacation', 'paternity', 'maternity', 'emergency']:
        vacation_days = str(number_of_days)
    elif leave_type == 'sick':
        sick_days = str(number_of_days)
    
    credits_header = [
        [Paragraph("<b>Vacation/others</b>", small_text),
         Paragraph("<b>Sick</b>", small_text),
         Paragraph("<b>Total</b>", small_text),
         Paragraph("<b>Remaining</b>", small_text)]
    ]
    
    credits_values = [
        [Paragraph(f"{vacation_days} days", small_text),
         Paragraph(f"{sick_days} days", small_text),
         Paragraph(f"{number_of_days} days", small_text),
         Paragraph(f"{leave_balance_after} days", small_text)]
    ]
    
    credits_table = Table(credits_header + credits_values, 
                         colWidths=[23*mm, 19*mm, 19*mm, 18.3*mm])
    credits_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    
    left_side_elements = [
        credits_table,
        Spacer(1, 2*mm),
        Paragraph("<i>Personnel Officer:</i>", small_text),
        Spacer(1, 2*mm),
        Paragraph("<u><b>JUNESSA CEZANNE REYES, RPm, CHRA</b></u>", centered_name_style),
        Paragraph("ACTING HR", centered_title_style),
        Spacer(1, 2*mm),
        Paragraph("<i>Approved for:</i>", small_text),
        Paragraph("_______ days with pay", centered_approved_style),
        Paragraph("_______ days without pay", centered_approved_style),
        Paragraph("_______ others (specify)", centered_approved_style)
    ]
    
    right_side_elements = [
        Paragraph("<b>RECOMMENDATION:</b>", small_text),
        Paragraph("[ ] Approval<br/>[ ] Disapproval due to", small_text_2),
        Spacer(1, 1*mm),
        Paragraph("__________________________________________________", centered_line_style2),
        Spacer(1, 6*mm),
        Paragraph("_________________________", centered_line_style),
        Spacer(1, 1*mm),
        Paragraph("<i>Authorized Official</i>", centered_title_style),
        Spacer(1, 4*mm),
        Paragraph("<i>Recommending approval:</i>", small_text),
        Spacer(1, 2*mm),
        Paragraph("<u><b>DR. FREDDIE T. BERNAL, CESO III</b></u>", centered_name_style),
        Paragraph("<i>Vice President for Academic Affairs</i>", centered_title_style)
    ]
    
    main_content_data = [[left_side_elements, right_side_elements]]
    main_content_table = Table(main_content_data, colWidths=[82*mm, 104*mm])
    main_content_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(main_content_table)
    
    story.append(Spacer(1, 3*mm))
    
    president_left_style = ParagraphStyle(
        'PresidentLeft',
        parent=small_text,
        alignment=TA_LEFT,
        leftIndent=45*mm,
    )
    
    story.append(Paragraph("<i>Approved by:</i>", president_left_style))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("<u><b>MIGUEL LUIS V. PELIÑO</b></u>", centered_name_style))
    story.append(Paragraph("<i>President</i>", centered_title_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer