# =========================================================
# salary_slip_report.py
# =========================================================

from io import BytesIO
from decimal import Decimal

from django.http import HttpResponse

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)

from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)

from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.units import mm


# =========================================================
# NUMBER TO WORDS
# =========================================================

def number_to_words(number):
    try:
        from num2words import num2words
        words = num2words(number, lang="en_IN").title()
        return f"Rupees {words} Only"
    except Exception:
        return f"Rupees {number} Only"


# =========================================================
# GENERATE SALARY SLIP
# Updated to match payroll_views.py context variables:
#   - per_day_salary   → based on gross (basic + hra + da)
#   - earned_basic_salary, earned_hra, earned_da → proportionate earned amounts
#   - attendance_deduction → absent + half_day + sunday_cut + 2nd_sat deduction
#   - absent_deduction, half_day_deduction, sunday_cut → breakdown of attendance deduction
#   - admin_deduction  → payroll.deductions (fixed admin deduction)
#   - total_deduction  → attendance_deduction + admin_deduction
#   - gross_salary     → basic + hra + da (full month, no bonus)
#   - net_salary       → earned_gross + bonus - admin_deduction
# =========================================================

def generate_salary_slip(
    employee,
    payroll,

    # Attendance counts
    present_days,
    absent_days,
    late_days,
    leave_days,
    half_day_days,

    # Calendar
    total_month_days,
    payable_days,
    cut_days,

    # Per day rates
    per_day_salary,
    half_day_salary,

    # Earned components
    earned_basic_salary,
    earned_hra,
    earned_da,

    # Deduction breakdown
    attendance_deduction,
    absent_deduction,
    half_day_deduction,
    sunday_cut,
    admin_deduction,
    total_deduction,

    # Totals
    gross_salary,
    net_salary,
):
    buffer = BytesIO()
    doc    = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=10,
        leftMargin=10,
        topMargin=10,
        bottomMargin=10,
    )

    styles   = getSampleStyleSheet()
    elements = []

    # -------------------------------------------------------
    # STYLES
    # -------------------------------------------------------
    center_style = ParagraphStyle(
        "center_style",
        parent=styles["BodyText"],
        alignment=TA_CENTER,
        fontSize=9,
        leading=14,
    )

    white_center = ParagraphStyle(
        "white_center",
        parent=styles["BodyText"],
        alignment=TA_CENTER,
        textColor=colors.white,
        fontSize=9,
        leading=14,
    )

    heading_style = ParagraphStyle(
        "heading_style",
        parent=styles["BodyText"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=colors.white,
    )

    title_style = ParagraphStyle(
        "title_style",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=colors.HexColor("#0F2C67"),
    )

    label_style = ParagraphStyle(
        "label_style",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
    )

    # -------------------------------------------------------
    # NAMES / WORDS
    # -------------------------------------------------------
    employee_name = (
        employee.user.get_full_name() or employee.user.username
    ).title()

    username     = employee.user.username.title()
    amount_words = number_to_words(int(net_salary))

    # -------------------------------------------------------
    # COMPANY HEADER
    # -------------------------------------------------------
    company_table = Table(
        [[
            Paragraph(
                """
                <font size="18"><b>MANTECH PUBLICATION PVT. LTD.</b></font>
                <br/><br/>
                <font size="9">C-56/11, Sector 62, Noida, Uttar Pradesh - 201309, India</font>
                <br/>
                <font size="9">Email : hr@mantechpublication.com</font>
                """,
                white_center
            )
        ]],
        colWidths=[190 * mm]
    )
    company_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#0F2C67")),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    elements.append(company_table)
    elements.append(Spacer(1, 10))

    # -------------------------------------------------------
    # TITLE
    # -------------------------------------------------------
    elements.append(Paragraph(
        f"<font size='15'><b>PAY SLIP FOR {payroll.month}/{payroll.year}</b></font>",
        title_style
    ))
    elements.append(Spacer(1, 12))

    # -------------------------------------------------------
    # EMPLOYEE DETAILS
    # -------------------------------------------------------
    employee_data = [
        ["Employee ID",        employee.emp_id,         "Username",         username],
        ["Employee Name",      employee_name,            "Email",            employee.user.email],
        ["Total Working Days", str(total_month_days),    "Payable Days",     str(payable_days)],
        ["Present Days",       str(present_days),        "Absent Days",      str(absent_days)],
        ["Late Days",          str(late_days),           "Leave Days",       str(leave_days)],
        ["Half Days",          str(half_day_days),       "Cut Days",         str(cut_days)],
        ["Per Day Salary",     f"Rs. {per_day_salary}",  "Half Day Salary",  f"Rs. {half_day_salary}"],
    ]

    emp_table = Table(employee_data, colWidths=[44*mm, 51*mm, 44*mm, 51*mm])
    emp_table.setStyle(TableStyle([
        ("GRID",          (0, 0), (-1, -1), 0.8, colors.HexColor("#CBD5E1")),
        ("BACKGROUND",    (0, 0), (0, -1),  colors.HexColor("#EFF6FF")),
        ("BACKGROUND",    (2, 0), (2, -1),  colors.HexColor("#EFF6FF")),
        ("FONTNAME",      (0, 0), (0, -1),  "Helvetica-Bold"),
        ("FONTNAME",      (2, 0), (2, -1),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    elements.append(emp_table)
    elements.append(Spacer(1, 16))

    # -------------------------------------------------------
    # SALARY BREAKDOWN
    # Earnings  → earned components (proportionate to days worked)
    # Deductions → broken down by type
    # -------------------------------------------------------
    salary_data = [
        # Header row
        [
            Paragraph("<b>EARNINGS</b>",   heading_style),
            Paragraph("<b>AMOUNT</b>",     heading_style),
            Paragraph("<b>DEDUCTIONS</b>", heading_style),
            Paragraph("<b>AMOUNT</b>",     heading_style),
        ],

        # Row 1
        [
            "Basic Salary (Full Month)",
            f"Rs. {payroll.basic_salary}",
            "Absent Deduction",
            f"Rs. {absent_deduction}",
        ],

        # Row 2
        [
            f"HRA ({payroll.hra_rate}% — Full Month)",
            f"Rs. {payroll.hra}",
            "Half Day Deduction",
            f"Rs. {half_day_deduction}",
        ],

        # Row 3
        [
            f"SA ({payroll.da_rate}% — Full Month)",
            f"Rs. {payroll.da}",
            "Sunday Cut",
            f"Rs. {sunday_cut}",
        ],

        # Row 4
        [
            "Earned Basic",
            f"Rs. {earned_basic_salary}",
            "Attendance Deduction",
            f"Rs. {attendance_deduction}",
        ],

        # Row 5
        [
            f"Earned HRA ({payroll.hra_rate}%)",
            f"Rs. {earned_hra}",
            "Admin Deduction",
            f"Rs. {admin_deduction} ({payroll.deduction_remark})" if payroll.deduction_remark else f"Rs. {admin_deduction}",
        ],

        # Row 6
        [
            f"Earned SA ({payroll.da_rate}%)",
            f"Rs. {earned_da}",
            "Total Deduction",
            f"Rs. {total_deduction}",
        ],

        # Row 7
        [
            "Bonus",
            f"Rs. {payroll.bonus} ({payroll.bonus_remark})" if payroll.bonus_remark else f"Rs. {payroll.bonus}",
            "",
            "",
        ],

        # Row 8 — Totals
        [
            "Gross Salary",
            f"Rs. {gross_salary}",
            "Net Salary",
            f"Rs. {net_salary}",
        ],
    ]

    sal_table = Table(salary_data, colWidths=[55*mm, 40*mm, 55*mm, 40*mm])
    sal_table.setStyle(TableStyle([
        # Header
        ("BACKGROUND",    (0, 0),  (-1, 0),  colors.HexColor("#0F2C67")),
        ("TEXTCOLOR",     (0, 0),  (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0),  (-1, 0),  "Helvetica-Bold"),

        # Grid
        ("GRID",          (0, 0),  (-1, -1), 0.8, colors.HexColor("#CBD5E1")),
        ("ALIGN",         (0, 0),  (-1, -1), "CENTER"),
        ("FONTSIZE",      (0, 0),  (-1, -1), 9),

        # Last row (totals) — bold + highlight
        ("FONTNAME",      (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND",    (0, -1), (-1, -1), colors.HexColor("#EFF6FF")),

        # Earned rows highlight (rows 4, 5, 6 → index 4, 5, 6)
        ("BACKGROUND",    (0, 4),  (1, 6),   colors.HexColor("#F0FDF4")),   # light green for earned
        ("BACKGROUND",    (2, 4),  (3, 6),   colors.HexColor("#FFF1F2")),   # light red for deductions

        # Padding
        ("BOTTOMPADDING", (0, 0),  (-1, -1), 8),
        ("TOPPADDING",    (0, 0),  (-1, -1), 8),
    ]))
    elements.append(sal_table)
    elements.append(Spacer(1, 16))

    # -------------------------------------------------------
    # NET SALARY BOX
    # -------------------------------------------------------
    net_table = Table(
        [[
            Paragraph(
                "<font color='white' size='12'><b>NET SALARY</b></font>",
                white_center
            ),
            Paragraph(
                f"<font color='white' size='13'><b>Rs. {net_salary}</b></font>",
                white_center
            ),
        ]],
        colWidths=[95*mm, 95*mm]
    )
    net_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#0F2C67")),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
    ]))
    elements.append(net_table)
    elements.append(Spacer(1, 14))

    # -------------------------------------------------------
    # AMOUNT IN WORDS
    # -------------------------------------------------------
    words_table = Table(
        [[
            Paragraph(
                f"<font size='9'><b>Amount In Words</b></font><br/><br/>"
                f"<font size='10'><b>{amount_words}</b></font>",
                center_style
            )
        ]],
        colWidths=[190 * mm]
    )
    words_table.setStyle(TableStyle([
        ("GRID",          (0, 0), (-1, -1), 0.8, colors.HexColor("#CBD5E1")),
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
    ]))
    elements.append(words_table)
    elements.append(Spacer(1, 20))

    # -------------------------------------------------------
    # FOOTER
    # -------------------------------------------------------
    elements.append(Paragraph(
        "<font size='8' color='#64748B'>This is a system-generated salary slip from Mantech Publication's "
        "HR Management System. Any discrepancies should be reported to the HR department within 7 working days.</font>",
        center_style
    ))

    # -------------------------------------------------------
    # BUILD PDF
    # -------------------------------------------------------
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


# =========================================================
# PDF RESPONSE
# =========================================================

def salary_slip_response(filename, pdf_data):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write(pdf_data)
    return response