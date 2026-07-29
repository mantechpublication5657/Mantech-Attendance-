# attendance/pdf_report.py

"""
Mantech Publication — Monthly Attendance PDF Report Generator
WITH HALF DAY SUPPORT
"""

import calendar
import io
from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.timezone import localdate

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm

from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .models import Attendance
from accounts.models import User


# =========================================================
# COLORS
# =========================================================

NAVY = colors.HexColor("#0B1E3D")
NAVY_MID = colors.HexColor("#1A3560")

ACCENT = colors.HexColor("#1D6FE8")
ACCENT_LT = colors.HexColor("#EEF4FF")

WHITE = colors.white
SILVER = colors.HexColor("#F4F7FC")

RULE = colors.HexColor("#D0DBF0")

TEXT_DARK = colors.HexColor("#0F1B2D")
TEXT_MID = colors.HexColor("#475569")
TEXT_LT = colors.HexColor("#94A3B8")


# =========================================================
# STATUS COLORS
# =========================================================

STATUS_COLORS = {

    "Present": (
        colors.HexColor("#D1FAE5"),
        colors.HexColor("#065F46")
    ),

    "Absent": (
        colors.HexColor("#FFE4E6"),
        colors.HexColor("#9F1239")
    ),

    "Late": (
        colors.HexColor("#FEF3C7"),
        colors.HexColor("#92400E")
    ),

    "Leave": (
        colors.HexColor("#DBEAFE"),
        colors.HexColor("#1E40AF")
    ),

    "Half Day": (
        colors.HexColor("#EDE9FE"),
        colors.HexColor("#6D28D9")
    ),
}


# =========================================================
# STYLES
# =========================================================

def _styles():

    base = getSampleStyleSheet()

    return {

        "company": ParagraphStyle(
            "company",
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=28,
            textColor=WHITE,
            alignment=TA_CENTER,
        ),

        "report_title": ParagraphStyle(
            "report_title",
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            textColor=colors.HexColor("#A8C4F0"),
            alignment=TA_CENTER,
        ),

        "report_period": ParagraphStyle(
            "report_period",
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=18,
            textColor=WHITE,
            alignment=TA_CENTER,
        ),

        "meta_value": ParagraphStyle(
            "meta_value",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=TEXT_DARK,
            alignment=TA_LEFT,
        ),

        "section_head": ParagraphStyle(
            "section_head",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=NAVY,
            alignment=TA_LEFT,
        ),

        "cell": ParagraphStyle(
            "cell",
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=TEXT_DARK,
            alignment=TA_CENTER,
        ),

        "cell_date": ParagraphStyle(
            "cell_date",
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=13,
            textColor=TEXT_DARK,
            alignment=TA_LEFT,
        ),

        "disclaimer": ParagraphStyle(
            "disclaimer",
            fontName="Helvetica-Oblique",
            fontSize=7.5,
            textColor=TEXT_LT,
            alignment=TA_CENTER,
        ),
    }


# =========================================================
# FOOTER
# =========================================================

class _HeaderFooter:

    def __init__(self, report_month, employee_name):

        self.month = report_month
        self.employee = employee_name

    def __call__(self, canvas, doc):

        canvas.saveState()

        w, h = A4

        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.5)

        canvas.line(
            18 * mm,
            14 * mm,
            w - 18 * mm,
            14 * mm
        )

        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(TEXT_LT)

        canvas.drawString(
            18 * mm,
            10 * mm,
            f"Mantech Publication | {self.employee} | {self.month}"
        )

        canvas.drawRightString(
            w - 18 * mm,
            10 * mm,
            f"Page {doc.page}"
        )

        canvas.restoreState()


# =========================================================
# MAIN PDF GENERATOR
# =========================================================

def generate_attendance_pdf(user, month, year):

    buf = io.BytesIO()

    st = _styles()

    month_name = calendar.month_name[month]

    report_period = f"{month_name} {year}"

    employee_name = (
        user.get_full_name().upper()
        or user.username.upper()
    )

    generated_on = date.today().strftime("%d %B %Y")

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=10 * mm,
        bottomMargin=22 * mm,
    )

    PAGE_W = A4[0] - 36 * mm

    story = []

    # =====================================================
    # HEADER
    # =====================================================

    banner = Table(
        [
            [Paragraph("MANTECH PUBLICATION", st["company"])],
            [Paragraph("Monthly Attendance Report", st["report_title"])],
            [Paragraph(report_period.upper(), st["report_period"])],
        ],
        colWidths=[PAGE_W],
    )

    banner.setStyle(TableStyle([

        ("BACKGROUND", (0, 0), (-1, -1), NAVY),

        ("ROWBACKGROUNDS",
         (0, 0),
         (-1, -1),
         [NAVY, NAVY, NAVY_MID]),

        ("TOPPADDING", (0, 0), (-1, -1), 12),

        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),

    ]))

    story.append(banner)

    story.append(Spacer(1, 6 * mm))

    # =====================================================
    # EMPLOYEE META
    # =====================================================

    meta = Table(
        [[

            Paragraph(
                f"<font color='#94A3B8'>Employee</font><br/>{employee_name}",
                st["meta_value"]
            ),

            Paragraph(
                f"<font color='#94A3B8'>Employee ID</font><br/>{user.employee_profile.emp_id}",
                st["meta_value"]
            ),

            Paragraph(
                f"<font color='#94A3B8'>Report Month</font><br/>{report_period}",
                st["meta_value"]
            ),

            Paragraph(
                f"<font color='#94A3B8'>Generated On</font><br/>{generated_on}",
                st["meta_value"]
            ),

        ]],

        colWidths=[PAGE_W / 4] * 4,
    )

    meta.setStyle(TableStyle([

        ("BACKGROUND", (0, 0), (-1, -1), SILVER),

        ("BOX", (0, 0), (-1, -1), 0.5, RULE),

        ("INNERGRID", (0, 0), (-1, -1), 0.4, RULE),

        ("TOPPADDING", (0, 0), (-1, -1), 8),

        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),

    ]))

    story.append(meta)

    story.append(Spacer(1, 5 * mm))

    # =====================================================
    # FETCH DATA
    # =====================================================

    qs = Attendance.objects.filter(
        employee=user,
        date__month=month,
        date__year=year
    ).order_by("date")

    present_count = 0
    absent_count = 0
    late_count = 0
    leave_count = 0
    half_day_count = 0
    sunday_count = 0

    for a in qs:

        if a.status == "Present":

            present_count += 1

        elif a.status == "Absent":

            absent_count += 1

        elif a.status == "Late":

            late_count += 1

        elif a.status == "Leave":

            leave_count += 1

        elif a.status == "Half Day":

            half_day_count += 1
            
        elif a.status == "Sunday":

            sunday_count += 1

    total = (
        present_count +
        absent_count +
        late_count +
        leave_count +
        half_day_count +
        sunday_count
    )
    
    payroll_days = present_count + late_count + leave_count + half_day_count/2 + sunday_count

    # =====================================================
    # SUMMARY TILES
    # =====================================================

    # def _tile(number, label, bg, fg):

    #     num_style = ParagraphStyle(
    #         "num",
    #         fontName="Helvetica-Bold",
    #         fontSize=22,
    #         alignment=TA_CENTER,
    #         textColor=fg,
    #     )

    #     lbl_style = ParagraphStyle(
    #         "lbl",
    #         fontName="Helvetica",
    #         fontSize=8,
    #         alignment=TA_CENTER,
    #         textColor=fg,
    #     )

    #     t = Table(
    #         [
    #             [Paragraph(str(number), num_style)],
    #             [Paragraph(label, lbl_style)]
    #         ],
    #         colWidths=[(PAGE_W / 5) - 4],
    #     )

    #     t.setStyle(TableStyle([

    #         ("BACKGROUND", (0, 0), (-1, -1), bg),

    #         ("TOPPADDING", (0, 0), (-1, -1), 12),

    #         ("BOTTOMPADDING", (0, 0), (-1, -1), 12),

    #     ]))

    #     return t

    # tiles = Table(
    #     [[

    #         _tile(
    #             present_count,
    #             "PRESENT",
    #             colors.HexColor("#D1FAE5"),
    #             colors.HexColor("#065F46")
    #         ),

    #         _tile(
    #             absent_count,
    #             "ABSENT",
    #             colors.HexColor("#FFE4E6"),
    #             colors.HexColor("#9F1239")
    #         ),

    #         _tile(
    #             late_count,
    #             "LATE",
    #             colors.HexColor("#FEF3C7"),
    #             colors.HexColor("#92400E")
    #         ),

    #         _tile(
    #             leave_count,
    #             "LEAVE",
    #             colors.HexColor("#DBEAFE"),
    #             colors.HexColor("#1E40AF")
    #         ),

    #         _tile(
    #             half_day_count,
    #             "HALF DAY",
    #             colors.HexColor("#EDE9FE"),
    #             colors.HexColor("#6D28D9")
    #         ),

    #     ]],

    #     colWidths=[(PAGE_W / 5) - 3] * 5,
    # )

    # story.append(tiles)

    # story.append(Spacer(1, 5 * mm))

    # =====================================================
    # TABLE HEADING
    # =====================================================

    story.append(
        Paragraph(
            "Attendance Records",
            st["section_head"]
        )
    )

    story.append(Spacer(1, 3 * mm))

    # =====================================================
    # TABLE
    # =====================================================

    headers = [
        "Date",
        "Day",
        "Check In",
        "Check Out",
        "Status",
    ]

    rows = [headers]

    for a in qs:

        status_bg, status_fg = STATUS_COLORS.get(
            a.status,
            (ACCENT_LT, NAVY)
        )

        # Change to:
        chip_label = (
            a.remarks
            if a.status == "Leave" and a.remarks
            else a.status
        )

        chip = Table(
            [[
                Paragraph(
                    chip_label,
                    ParagraphStyle(
                        "chip",
                        fontName="Helvetica-Bold",
                        fontSize=8,
                        alignment=TA_CENTER,
                        textColor=status_fg,
                    )
                )
            ]],
            colWidths=[35 * mm],
        )
        
        chip.setStyle(TableStyle([

            ("BACKGROUND", (0, 0), (-1, -1), status_bg),

            ("TOPPADDING", (0, 0), (-1, -1), 3),

            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),

        ]))

        rows.append([

            Paragraph(
                a.date.strftime("%d %b %Y"),
                st["cell_date"]
            ),

            Paragraph(
                a.date.strftime("%A"),
                st["cell"]
            ),

            Paragraph(
                a.check_in.strftime("%I:%M %p")
                if a.check_in else "—",
                st["cell"]
            ),

            Paragraph(
                a.check_out.strftime("%I:%M %p")
                if a.check_out else "—",
                st["cell"]
            ),

            chip,
        ])

    table = Table(
        rows,
        colWidths=[
            35 * mm,
            30 * mm,
            30 * mm,
            30 * mm,
            50 * mm,   # ← wider for remarks text
        ],
        repeatRows=1,
    )

    table.setStyle(TableStyle([

        ("BACKGROUND", (0, 0), (-1, 0), NAVY),

        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),

        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),

        ("FONTSIZE", (0, 0), (-1, 0), 9),

        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),

        ("TOPPADDING", (0, 0), (-1, 0), 10),

        ("GRID", (0, 0), (-1, -1), 0.4, RULE),

        ("BACKGROUND",
         (0, 1),
         (-1, -1),
         colors.HexColor("#F8FAFF")),

        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        ("ALIGN", (1, 1), (-1, -1), "CENTER"),

    ]))

    story.append(table)

    story.append(Spacer(1, 5 * mm))

    # =====================================================
    # TOTALS
    # =====================================================

    totals = Table(
        [[

            Paragraph(

                f"<b>Total Records:</b> {total}"
                f" &nbsp;&nbsp; "
                f"<b>Present:</b> {present_count}"
                f" &nbsp;&nbsp; "
                f"<b>Absent:</b> {absent_count}"
                f" &nbsp;&nbsp; "
                f"<b>Late:</b> {late_count}"
                f" &nbsp;&nbsp; "
                f"<b>Leave:</b> {leave_count}"
                f" &nbsp;&nbsp; "
                f"<b>Half Day:</b> {half_day_count}"
                f" &nbsp;&nbsp; "
                f"<b>Sunday:</b> {sunday_count}"
                f" &nbsp;&nbsp; "
                f"<b>Payroll Days:</b> {payroll_days}",

                ParagraphStyle(
                    "totals",
                    fontName="Helvetica",
                    fontSize=9,
                    textColor=NAVY,
                    alignment=TA_LEFT,
                )
            )

        ]],

        colWidths=[PAGE_W],
    )

    totals.setStyle(TableStyle([

        ("BACKGROUND", (0, 0), (-1, -1), ACCENT_LT),

        ("BOX", (0, 0), (-1, -1), 0.5, ACCENT),

        ("TOPPADDING", (0, 0), (-1, -1), 8),

        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),

    ]))

    story.append(totals)

    story.append(Spacer(1, 10 * mm))

    # =====================================================
    # DISCLAIMER
    # =====================================================

    story.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=RULE
        )
    )

    story.append(Spacer(1, 2 * mm))

    story.append(

        Paragraph(

            "This is a system generated attendance report from "
            "Mantech Publication HRMS.",

            st["disclaimer"]
        )
    )

    # =====================================================
    # BUILD
    # =====================================================

    hf = _HeaderFooter(
        report_period,
        employee_name
    )

    doc.build(
        story,
        onFirstPage=hf,
        onLaterPages=hf
    )

    buf.seek(0)

    return buf.read()


# =========================================================
# DOWNLOAD VIEW
# =========================================================

@login_required
def download_attendance_pdf(request, user_id):

    today = localdate()

    month_raw = request.GET.get("month", "").strip()
    year_raw = request.GET.get("year", "").strip()

    month = int(month_raw) if month_raw.isdigit() else today.month
    year = int(year_raw) if year_raw.isdigit() else today.year

    employee = get_object_or_404(
        User,
        id=user_id
    )

    pdf_bytes = generate_attendance_pdf(
        employee,
        month,
        year
    )

    filename = (
        f"attendance_"
        f"{calendar.month_name[month]}_"
        f"{year}_"
        f"{employee.username}.pdf"
    )

    response = HttpResponse(
        pdf_bytes,
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'attachment; filename="{filename}"'
    )

    return response