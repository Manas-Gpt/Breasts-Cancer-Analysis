"""
PDF Report Generator for Breast Cancer Analysis.
Generates a professional medical-style PDF patient report.
"""
import io
import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, Image as RLImage
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.platypus.flowables import Flowable

# Color palette
DARK_BLUE   = colors.HexColor('#0F172A')
MED_BLUE    = colors.HexColor('#1E3A5F')
ACCENT_BLUE = colors.HexColor('#2563EB')
LIGHT_BLUE  = colors.HexColor('#EFF6FF')
GREEN       = colors.HexColor('#16A34A')
YELLOW      = colors.HexColor('#D97706')
RED         = colors.HexColor('#DC2626')
GRAY_LIGHT  = colors.HexColor('#F1F5F9')
GRAY_MID    = colors.HexColor('#94A3B8')
GRAY_DARK   = colors.HexColor('#334155')
WHITE       = colors.white

CLASS_COLORS = {
    'Normal':    GREEN,
    'Benign':    YELLOW,
    'Malignant': RED,
}

CLASS_BG = {
    'Normal':    colors.HexColor('#DCFCE7'),
    'Benign':    colors.HexColor('#FEF3C7'),
    'Malignant': colors.HexColor('#FEE2E2'),
}

def generate_pdf_report(data: dict) -> io.BytesIO:
    """Generate a full breast cancer analysis PDF report."""
    buf = io.BytesIO()

    patient  = data.get('patient', {})
    result   = data.get('result', {})
    exam     = data.get('exam', {})
    images   = data.get('images', [])  # base64 encoded images

    label      = result.get('label', 'Unknown')
    probs      = result.get('probabilities', {})
    risk_score = result.get('risk_score', 0)
    confidence = result.get('confidence', 0)
    risk_level = result.get('risk_level', 'N/A')
    recommendation = result.get('recommendation', '')

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=15*mm, bottomMargin=20*mm,
        leftMargin=20*mm, rightMargin=20*mm,
        title="Breast Cancer Analysis Report"
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle('Title', parent=styles['Title'],
        fontSize=20, textColor=WHITE, alignment=TA_CENTER, spaceAfter=0,
        fontName='Helvetica-Bold')

    subtitle_style = ParagraphStyle('Sub', parent=styles['Normal'],
        fontSize=10, textColor=colors.HexColor('#93C5FD'), alignment=TA_CENTER,
        fontName='Helvetica')

    section_header = ParagraphStyle('SecHead', parent=styles['Normal'],
        fontSize=12, textColor=ACCENT_BLUE, spaceAfter=6, spaceBefore=12,
        fontName='Helvetica-Bold', borderPadding=(0, 0, 4, 0))

    body_style = ParagraphStyle('Body', parent=styles['Normal'],
        fontSize=9, textColor=GRAY_DARK, leading=14, fontName='Helvetica',
        spaceAfter=4)

    label_style = ParagraphStyle('Label', parent=styles['Normal'],
        fontSize=8, textColor=GRAY_MID, fontName='Helvetica-Bold',
        spaceBefore=0, spaceAfter=1)

    value_style = ParagraphStyle('Value', parent=styles['Normal'],
        fontSize=10, textColor=DARK_BLUE, fontName='Helvetica',
        spaceBefore=0, spaceAfter=6)

    disclaimer_style = ParagraphStyle('Disc', parent=styles['Normal'],
        fontSize=7, textColor=GRAY_MID, fontName='Helvetica-Oblique',
        leading=10, alignment=TA_JUSTIFY)

    story = []

    # ─── HEADER BANNER ───────────────────────────────────────────────────────
    header_data = [
        [Paragraph("🔬 Breast Cancer Analysis Report", title_style)],
        [Paragraph("AI-Assisted Mammography Classification System | Confidential Medical Document", subtitle_style)],
    ]
    header_table = Table(header_data, colWidths=[170*mm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), MED_BLUE),
        ('TOPPADDING',    (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,1), (-1,1), 12),
        ('LEFTPADDING',   (0,0), (-1,-1), 8),
        ('RIGHTPADDING',  (0,0), (-1,-1), 8),
        ('ROUNDEDCORNERS', [6]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8*mm))

    # ─── Report meta row ─────────────────────────────────────────────────────
    now = datetime.datetime.now()
    report_id = f"BCR-{now.strftime('%Y%m%d%H%M%S')}"
    meta_data = [
        [Paragraph("Report ID", label_style), Paragraph("Date & Time", label_style),
         Paragraph("Analysis Type", label_style), Paragraph("Status", label_style)],
        [Paragraph(report_id, value_style),
         Paragraph(now.strftime('%d %b %Y  %H:%M'), value_style),
         Paragraph("Mammography AI", value_style),
         Paragraph("✓ Complete", ParagraphStyle('ok', parent=value_style, textColor=GREEN))],
    ]
    meta_tbl = Table(meta_data, colWidths=[45*mm, 45*mm, 45*mm, 35*mm])
    meta_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), GRAY_LIGHT),
        ('GRID',          (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING',    (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING',   (0,0), (-1,-1), 6),
        ('ROUNDEDCORNERS', [4]),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 6*mm))

    # ─── PATIENT INFO ─────────────────────────────────────────────────────────
    story.append(Paragraph("Patient Information", section_header))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT_BLUE, spaceAfter=6))

    p = patient
    patient_data = [
        [Paragraph("Full Name", label_style),   Paragraph("Date of Birth", label_style),
         Paragraph("Age", label_style),          Paragraph("Gender", label_style)],
        [Paragraph(p.get('name', 'N/A'), value_style),
         Paragraph(p.get('dob', 'N/A'), value_style),
         Paragraph(str(p.get('age', 'N/A')), value_style),
         Paragraph(p.get('gender', 'Female'), value_style)],
        [Paragraph("Patient ID", label_style),   Paragraph("Referring Physician", label_style),
         Paragraph("Contact", label_style),       Paragraph("Exam Date", label_style)],
        [Paragraph(p.get('id', 'N/A'), value_style),
         Paragraph(p.get('physician', 'N/A'), value_style),
         Paragraph(p.get('contact', 'N/A'), value_style),
         Paragraph(exam.get('date', now.strftime('%d %b %Y')), value_style)],
    ]
    patient_tbl = Table(patient_data, colWidths=[42.5*mm]*4)
    patient_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), WHITE),
        ('BOX',           (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('GRID',          (0,0), (-1,-1), 0.3, colors.HexColor('#E2E8F0')),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING',   (0,0), (-1,-1), 8),
        ('BACKGROUND',    (0,0), (-1,0), GRAY_LIGHT),
        ('BACKGROUND',    (0,2), (-1,2), GRAY_LIGHT),
    ]))
    story.append(patient_tbl)
    story.append(Spacer(1, 6*mm))

    # ─── CLASSIFICATION RESULT ────────────────────────────────────────────────
    story.append(Paragraph("Classification Result", section_header))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT_BLUE, spaceAfter=6))

    result_color = CLASS_COLORS.get(label, GRAY_DARK)
    result_bg    = CLASS_BG.get(label, GRAY_LIGHT)

    # Big result box
    result_style = ParagraphStyle('ResultBig', parent=styles['Normal'],
        fontSize=22, textColor=result_color, alignment=TA_CENTER,
        fontName='Helvetica-Bold', spaceAfter=0)
    verdict_style = ParagraphStyle('Verdict', parent=styles['Normal'],
        fontSize=10, textColor=GRAY_DARK, alignment=TA_CENTER,
        fontName='Helvetica', spaceAfter=0)

    icons = {'Normal': '✅', 'Benign': '⚠️', 'Malignant': '🚨'}
    icon = icons.get(label, '🔬')

    result_box_data = [
        [Paragraph(f"{icon}  {label.upper()}", result_style)],
        [Paragraph(f"Confidence: {confidence*100:.1f}%  |  Risk Level: {risk_level}", verdict_style)],
    ]
    result_box = Table(result_box_data, colWidths=[170*mm])
    result_box.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), result_bg),
        ('BOX',           (0,0), (-1,-1), 2, result_color),
        ('TOPPADDING',    (0,0), (-1,0), 14),
        ('BOTTOMPADDING', (0,1), (-1,1), 14),
        ('ROUNDEDCORNERS', [8]),
    ]))
    story.append(result_box)
    story.append(Spacer(1, 5*mm))

    # ─── PROBABILITY BREAKDOWN ────────────────────────────────────────────────
    story.append(Paragraph("Probability Distribution", section_header))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT_BLUE, spaceAfter=6))

    def prob_bar_table(label_name, prob, color):
        bar_width = int(prob * 140)  # max 140mm
        pct = f"{prob*100:.1f}%"
        bar_data = [[
            Paragraph(label_name, ParagraphStyle('bl', fontSize=9, fontName='Helvetica-Bold',
                textColor=GRAY_DARK, alignment=TA_LEFT)),
            Paragraph(pct, ParagraphStyle('bp', fontSize=9, fontName='Helvetica-Bold',
                textColor=color, alignment=TA_RIGHT)),
        ]]
        bar_tbl = Table(bar_data, colWidths=[80*mm, 90*mm])
        bar_tbl.setStyle(TableStyle([
            ('TOPPADDING',    (0,0), (-1,-1), 1),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ]))

        # Progress-bar simulation using colored/gray cells
        prog_data = [['', '']]
        prog_tbl = Table(prog_data, colWidths=[bar_width*mm/10 if bar_width > 0 else 1, (140 - bar_width)*mm/10 + 30*mm])
        prog_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (0,0), color),
            ('BACKGROUND',    (1,0), (1,0), colors.HexColor('#E2E8F0')),
            ('TOPPADDING',    (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('ROUNDEDCORNERS', [3]),
        ]))
        return bar_tbl, prog_tbl

    for cat, col in [('normal', GREEN), ('benign', YELLOW), ('malignant', RED)]:
        prob = probs.get(cat, 0)
        lbl = cat.capitalize()
        tbl1, tbl2 = prob_bar_table(lbl, prob, col)
        story.append(tbl1)
        story.append(tbl2)
        story.append(Spacer(1, 2*mm))

    story.append(Spacer(1, 4*mm))

    # ─── RISK SCORE CARD ──────────────────────────────────────────────────────
    risk_pct = int(risk_score * 100)
    risk_col = RED if risk_pct > 60 else (YELLOW if risk_pct > 30 else GREEN)
    risk_card_data = [
        [Paragraph("Overall Risk Score", ParagraphStyle('rl', fontSize=10,
            fontName='Helvetica-Bold', textColor=GRAY_DARK, alignment=TA_CENTER)),
         Paragraph("Risk Category", ParagraphStyle('rl', fontSize=10,
            fontName='Helvetica-Bold', textColor=GRAY_DARK, alignment=TA_CENTER))],
        [Paragraph(f"{risk_pct}/100", ParagraphStyle('rv', fontSize=20,
            fontName='Helvetica-Bold', textColor=risk_col, alignment=TA_CENTER)),
         Paragraph(risk_level, ParagraphStyle('rv', fontSize=20,
            fontName='Helvetica-Bold', textColor=risk_col, alignment=TA_CENTER))],
    ]
    risk_card = Table(risk_card_data, colWidths=[85*mm, 85*mm])
    risk_card.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0), GRAY_LIGHT),
        ('BACKGROUND',    (0,1), (-1,1), WHITE),
        ('BOX',           (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('LINEAFTER',     (0,0), (0,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING',    (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('ROUNDEDCORNERS', [4]),
    ]))
    story.append(risk_card)
    story.append(Spacer(1, 6*mm))

    # ─── RECOMMENDATION ───────────────────────────────────────────────────────
    story.append(Paragraph("Clinical Recommendation", section_header))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT_BLUE, spaceAfter=6))

    rec_data = [[Paragraph(recommendation or 'Consult your physician.', body_style)]]
    rec_tbl = Table(rec_data, colWidths=[170*mm])
    rec_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), result_bg),
        ('LEFTPADDING',   (0,0), (-1,-1), 12),
        ('RIGHTPADDING',  (0,0), (-1,-1), 12),
        ('TOPPADDING',    (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('BOX',           (0,0), (-1,-1), 1.5, result_color),
        ('ROUNDEDCORNERS', [6]),
    ]))
    story.append(rec_tbl)
    story.append(Spacer(1, 6*mm))

    # ─── EXAM DETAILS ─────────────────────────────────────────────────────────
    story.append(Paragraph("Exam Details", section_header))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT_BLUE, spaceAfter=6))

    exam_details = [
        ['Exam Type',       exam.get('type', 'Mammography Screening')],
        ['Facility',        exam.get('facility', 'AI Diagnostic Center')],
        ['Exam Date',       exam.get('date', now.strftime('%d %b %Y'))],
        ['Analysis Model',  'NYU-Inspired ResNet Classifier (v2.1)'],
        ['Views Analyzed',  'L-CC, L-MLO, R-CC, R-MLO'],
        ['Processing Time', exam.get('processing_time', '< 2 seconds')],
    ]
    exam_rows = []
    for k, v in exam_details:
        exam_rows.append([
            Paragraph(k, label_style),
            Paragraph(v, body_style)
        ])
    exam_tbl = Table(exam_rows, colWidths=[55*mm, 115*mm])
    exam_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), WHITE),
        ('GRID',          (0,0), (-1,-1), 0.3, colors.HexColor('#E2E8F0')),
        ('BACKGROUND',    (0,0), (0,-1), GRAY_LIGHT),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING',   (0,0), (-1,-1), 8),
        ('ROUNDEDCORNERS', [4]),
    ]))
    story.append(exam_tbl)
    story.append(Spacer(1, 8*mm))

    # ─── FOOTER DISCLAIMER ────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY_MID, spaceAfter=4))
    disclaimer = (
        "⚠ DISCLAIMER: This report has been generated by an artificial intelligence system for research and educational purposes only. "
        "It is NOT a substitute for professional medical advice, diagnosis, or treatment. "
        "Always consult a qualified healthcare professional before making any medical decisions. "
        "The AI model referenced in this report is inspired by the NYU Breast Cancer Classifier (Shen et al., 2019) "
        'and trained on publicly available research data. Report ID: ' + report_id
    )
    story.append(Paragraph(disclaimer, disclaimer_style))

    doc.build(story)
    return buf
