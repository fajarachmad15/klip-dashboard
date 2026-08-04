"""
Module: pdf_generator.py
Deskripsi: Utility untuk meng-generate Laporan Executive KLIP 2026 dalam format PDF (ReportLab).
"""

import io
import datetime
import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Canvas kustom untuk menambahkan footer halaman 'Page X of Y' dan footer rahasia perusahaan."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Footer Line
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(36, 36, 559, 36)

        # Footer text
        footer_text = "KLIP Finance Analytics Dashboard 2026 • Executive Performance Report"
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawString(36, 24, footer_text)
        self.drawRightString(559, 24, page_str)
        self.restoreState()


def create_cell(text, style, align="left"):
    """Helper untuk membungkus teks dalam Paragraph sel tabel."""
    return Paragraph(str(text), style)


def generate_klip_pdf_report(scope: str, df_eng: pd.DataFrame = None, df_fas: pd.DataFrame = None, df_sub: pd.DataFrame = None) -> bytes:
    """
    Meng-generate PDF Laporan KLIP 2026 berdasarkan scope ('Semua Halaman', 'Detail Engagement 2026', dst.)
    Returns byte content dari file PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=48,
    )

    styles = getSampleStyleSheet()

    # Custom Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1E3A8A'),
    )
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#475569'),
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=10,
        spaceAfter=6,
    )
    th_style = ParagraphStyle(
        'THeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=10,
        textColor=colors.white,
        alignment=1, # Center
    )
    td_left = ParagraphStyle(
        'TDataLeft',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#0F172A'),
    )
    td_center = ParagraphStyle(
        'TDataCenter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#0F172A'),
        alignment=1,
    )
    td_bold_center = ParagraphStyle(
        'TDataBoldCenter',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1E3A8A'),
        alignment=1,
    )

    story = []

    # -------------------------------------------------------------------------
    # HEADER BANNER
    # -------------------------------------------------------------------------
    story.append(create_cell("KLIP EXECUTIVE PERFORMANCE REPORT 2026", title_style))
    now_str = datetime.datetime.now().strftime("%d %B %Y, %H:%M WIB")
    story.append(create_cell(f"Scope: {scope} | Generated: {now_str} | Confidential Corporate Report", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2563EB"), spaceAfter=12))

    show_all = scope == "Semua Halaman" or scope == "All Pages"
    has_page_added = False

    # -------------------------------------------------------------------------
    # SECTION 1: DETAIL ENGAGEMENT 2026
    # -------------------------------------------------------------------------
    if show_all or scope == "Detail Engagement 2026":
        story.append(create_cell("📊 1. Detail Engagement 2026", section_heading))
        
        if df_eng is not None and not df_eng.empty:
            tot_emp = len(df_eng)
            eng_emp = len(df_eng[df_eng.get("Engagement_Status", pd.Series()) == "Engaged"])
            non_eng_emp = len(df_eng[df_eng.get("Engagement_Status", pd.Series()) == "Non-Engaged"])
            part_rate = (eng_emp / tot_emp * 100) if tot_emp > 0 else 0.0
            avg_score = df_eng["Engagement_Score"].mean() if "Engagement_Score" in df_eng.columns and tot_emp > 0 else 0.0

            # KPI Summary Table
            kpi_data = [
                [create_cell("Total Employees", th_style), create_cell("Engaged Employees", th_style), create_cell("Non-Engaged Employees", th_style), create_cell("Participation Rate", th_style), create_cell("Avg Engagement Score", th_style)],
                [create_cell(f"{tot_emp:,}", td_bold_center), create_cell(f"{eng_emp:,}", td_center), create_cell(f"{non_eng_emp:,}", td_center), create_cell(f"{part_rate:.1f}%", td_bold_center), create_cell(f"{avg_score:.1f} / 100", td_center)],
            ]
            t_kpi = Table(kpi_data, colWidths=[104, 104, 104, 104, 107])
            t_kpi.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563EB')),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
                ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
            ]))
            story.append(t_kpi)
            story.append(Spacer(1, 10))

            # Division Breakdown Table
            if "Division" in df_eng.columns:
                story.append(create_cell("<b>Division Engagement Performance</b>", section_heading))
                div_total = df_eng.groupby("Division").size().reset_index(name="Total")
                div_eng = df_eng[df_eng["Engagement_Status"] == "Engaged"].groupby("Division").size().reset_index(name="Engaged")
                merged_div = pd.merge(div_total, div_eng, on="Division", how="left").fillna(0)
                merged_div["NonEngaged"] = merged_div["Total"] - merged_div["Engaged"]
                merged_div["PartRate"] = (merged_div["Engaged"] / merged_div["Total"] * 100).round(1)
                merged_div = merged_div.sort_values(by="Total", ascending=False)

                div_rows = [
                    [create_cell("Division Name", th_style), create_cell("Total Employees", th_style), create_cell("Engaged", th_style), create_cell("Non-Engaged", th_style), create_cell("Participation %", th_style)]
                ]
                for _, r in merged_div.iterrows():
                    div_rows.append([
                        create_cell(r["Division"], td_left),
                        create_cell(f"{int(r['Total']):,}", td_center),
                        create_cell(f"{int(r['Engaged']):,}", td_center),
                        create_cell(f"{int(r['NonEngaged']):,}", td_center),
                        create_cell(f"{r['PartRate']:.1f}%", td_bold_center if r["PartRate"] >= 80 else td_center),
                    ])

                t_div = Table(div_rows, colWidths=[183, 85, 85, 85, 85])
                t_div.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                    ('TOPPADDING', (0,0), (-1,-1), 4),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
                ]))
                story.append(t_div)
        else:
            story.append(create_cell("No engagement data available.", td_left))

        has_page_added = True

    # -------------------------------------------------------------------------
    # SECTION 2: FASILITATOR CORPORATE
    # -------------------------------------------------------------------------
    if show_all or scope == "Fasilitator Corporate":
        if has_page_added:
            story.append(PageBreak())
            story.append(create_cell("KLIP EXECUTIVE PERFORMANCE REPORT 2026", title_style))
            story.append(create_cell(f"Scope: {scope} | Generated: {now_str}", subtitle_style))
            story.append(Spacer(1, 8))
            story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2563EB"), spaceAfter=12))

        story.append(create_cell("👥 2. Fasilitator Corporate Performance", section_heading))

        if df_fas is not None and not df_fas.empty:
            tot_fas = len(df_fas)
            tot_sub = int(df_fas["Submitted 2026"].sum()) if "Submitted 2026" in df_fas.columns else 0
            tot_reg = int(df_fas["Registered 2026"].sum()) if "Registered 2026" in df_fas.columns else 0
            tot_fin = int(df_fas["Finished 2026"].sum()) if "Finished 2026" in df_fas.columns else 0
            overall_pct = (tot_fin / tot_reg * 100) if tot_reg > 0 else 0.0

            fas_kpi = [
                [create_cell("Total Facilitators", th_style), create_cell("Submitted 2026", th_style), create_cell("Registered 2026", th_style), create_cell("Finished 2026", th_style), create_cell("Overall % Finished", th_style)],
                [create_cell(f"{tot_fas:,}", td_bold_center), create_cell(f"{tot_sub:,}", td_center), create_cell(f"{tot_reg:,}", td_center), create_cell(f"{tot_fin:,}", td_bold_center), create_cell(f"{overall_pct:.2f}%", td_bold_center)],
            ]
            t_fas_kpi = Table(fas_kpi, colWidths=[104, 104, 104, 104, 107])
            t_fas_kpi.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563EB')),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
                ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
            ]))
            story.append(t_fas_kpi)
            story.append(Spacer(1, 10))

            # Facilitator Performance Table
            story.append(create_cell("<b>Facilitator Performance List</b>", section_heading))
            fas_cols = ["Nama", "Function", "Submitted 2026", "Registered 2026", "Finished 2026"]
            fas_list_rows = [
                [create_cell("Facilitator Name", th_style), create_cell("Division", th_style), create_cell("Submitted", th_style), create_cell("Registered", th_style), create_cell("Finished", th_style), create_cell("% Finished", th_style)]
            ]

            df_fas_sorted = df_fas.sort_values(by="Finished 2026", ascending=False) if "Finished 2026" in df_fas.columns else df_fas
            for _, r in df_fas_sorted.head(20).iterrows():
                reg = int(r.get("Registered 2026", 0))
                fin = int(r.get("Finished 2026", 0))
                pct_str = f"{(fin / reg * 100):.2f}%" if reg > 0 else "0.00%"
                fas_list_rows.append([
                    create_cell(r.get("Nama", "-"), td_left),
                    create_cell(r.get("Function", "-"), td_left),
                    create_cell(int(r.get("Submitted 2026", 0)), td_center),
                    create_cell(reg, td_center),
                    create_cell(fin, td_center),
                    create_cell(pct_str, td_bold_center if fin > 0 else td_center),
                ])

            t_fas_list = Table(fas_list_rows, colWidths=[130, 113, 70, 70, 70, 70])
            t_fas_list.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
            ]))
            story.append(t_fas_list)
        else:
            story.append(create_cell("No facilitator data available.", td_left))

        has_page_added = True

    # -------------------------------------------------------------------------
    # SECTION 3: SUBMISSION 2026
    # -------------------------------------------------------------------------
    if show_all or scope == "Submission 2026":
        if has_page_added:
            story.append(PageBreak())
            story.append(create_cell("KLIP EXECUTIVE PERFORMANCE REPORT 2026", title_style))
            story.append(create_cell(f"Scope: {scope} | Generated: {now_str}", subtitle_style))
            story.append(Spacer(1, 8))
            story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2563EB"), spaceAfter=12))

        story.append(create_cell("📑 3. Submission 2026 Status & Category Matrix", section_heading))

        if df_sub is not None and not df_sub.empty:
            tot_sub_proj = len(df_sub)
            reg_proj = len(df_sub[df_sub.get("Stage", pd.Series()).isin(["IMPLEMENTATION", "CLOSING", "FINISHED"])])
            fin_proj = len(df_sub[df_sub.get("Stage", pd.Series()) == "FINISHED"])
            sub_fin_pct = (fin_proj / reg_proj * 100) if reg_proj > 0 else 0.0

            sub_kpi = [
                [create_cell("Total Submissions", th_style), create_cell("Registered Projects", th_style), create_cell("Finished Projects", th_style), create_cell("% Finished Rate", th_style)],
                [create_cell(f"{tot_sub_proj:,}", td_bold_center), create_cell(f"{reg_proj:,}", td_center), create_cell(f"{fin_proj:,}", td_bold_center), create_cell(f"{sub_fin_pct:.2f}%", td_bold_center)],
            ]
            t_sub_kpi = Table(sub_kpi, colWidths=[130, 130, 130, 133])
            t_sub_kpi.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563EB')),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
                ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
            ]))
            story.append(t_sub_kpi)
            story.append(Spacer(1, 10))

            # Category YoY Matrix
            story.append(create_cell("<b>Category Breakdown YoY Matrix</b>", section_heading))
            cat_rows = [
                [create_cell("Category", th_style), create_cell("Submission", th_style), create_cell("Registered", th_style), create_cell("Finished", th_style), create_cell("% Finished", th_style)]
            ]

            for cat in ["SLIM", "ACT"]:
                sub_c = len(df_sub[df_sub["Category"] == cat])
                reg_c = len(df_sub[(df_sub["Category"] == cat) & (df_sub["Stage"].isin(["IMPLEMENTATION", "CLOSING", "FINISHED"]))])
                fin_c = len(df_sub[(df_sub["Category"] == cat) & (df_sub["Stage"] == "FINISHED")])
                pct_c = f"{(fin_c / reg_c * 100):.2f}%" if reg_c > 0 else "0.00%"
                cat_rows.append([
                    create_cell(cat, td_left),
                    create_cell(sub_c, td_center),
                    create_cell(reg_c, td_center),
                    create_cell(fin_c, td_center),
                    create_cell(pct_c, td_bold_center),
                ])

            tot_cat_pct = f"{(fin_proj / reg_proj * 100):.2f}%" if reg_proj > 0 else "0.00%"
            cat_rows.append([
                create_cell("Total Overall", ParagraphStyle('TDataBoldLeft', parent=td_left, fontName='Helvetica-Bold', textColor=colors.HexColor('#1E3A8A'))),
                create_cell(tot_sub_proj, td_bold_center),
                create_cell(reg_proj, td_bold_center),
                create_cell(fin_proj, td_bold_center),
                create_cell(tot_cat_pct, td_bold_center),
            ])

            t_cat = Table(cat_rows, colWidths=[123, 100, 100, 100, 100])
            t_cat.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
                ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#EFF6FF')),
            ]))
            story.append(t_cat)
            story.append(Spacer(1, 10))

            # Top Projects Table
            story.append(create_cell("<b>Sample Submission Projects Detail</b>", section_heading))
            proj_rows = [
                [create_cell("No. KLIP", th_style), create_cell("Category", th_style), create_cell("Project Title", th_style), create_cell("Leader Name", th_style), create_cell("Stage", th_style)]
            ]

            display_cols = ["No.KLIP", "Category", "Title", "Leader_Name", "Stage"]
            for _, r in df_sub.head(15).iterrows():
                proj_rows.append([
                    create_cell(r.get("No.KLIP", "-"), td_left),
                    create_cell(r.get("Category", "-"), td_center),
                    create_cell(r.get("Title", "-"), td_left),
                    create_cell(r.get("Leader_Name", "-"), td_left),
                    create_cell(r.get("Stage", "-"), td_center),
                ])

            t_proj = Table(proj_rows, colWidths=[90, 60, 203, 110, 60])
            t_proj.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563EB')),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
            ]))
            story.append(t_proj)
        else:
            story.append(create_cell("No submission data available.", td_left))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()
