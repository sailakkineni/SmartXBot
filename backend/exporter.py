import io
from io import BytesIO
import re
from typing import Optional
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

BULLET_PREFIX_REGEX = re.compile(r"^[\s\t]*([•\-*o▪■‣⁃–—\u2022\u25aa\u25a0\u2023\u2043\u2013\u2014\uf0a7\uf0b7\uf0a8]|\d+[\.\)])\s*")

def update_docx_paragraph_safely(para: docx.text.paragraph.Paragraph, orig_text: str, tail_text: str) -> bool:
    """
    Safely updates target bullet text within a Word paragraph,
    preserving 100% of paragraph formatting, fonts, tab stops, and trailing date/location runs.
    """
    full_text = para.text.strip()
    if not full_text:
        return False
        
    # Clean bullet symbols from original and paragraph text for matching
    clean_orig = BULLET_PREFIX_REGEX.sub("", orig_text).strip()
    clean_para = BULLET_PREFIX_REGEX.sub("", full_text).strip()
    
    norm_orig = re.sub(r"[^a-zA-Z0-9]", "", clean_orig).lower()
    norm_para = re.sub(r"[^a-zA-Z0-9]", "", clean_para).lower()
    
    if not norm_orig or not norm_para or len(norm_orig) < 10:
        return False
        
    # Match criteria: exact match or high string overlap
    is_match = (norm_orig == norm_para) or (len(norm_orig) > 15 and norm_orig in norm_para) or (len(norm_para) > 15 and norm_para in norm_orig)
    if not is_match:
        return False
        
    clean_tail = BULLET_PREFIX_REGEX.sub("", tail_text).strip()
    if not clean_tail:
        clean_tail = tail_text.strip()
        
    style_name = str(getattr(para.style, "name", "")).lower()
    is_list_style = "list" in style_name or "bullet" in style_name
    
    # Detect leading bullet symbol of paragraph if not a Word List style
    bullet_prefix = ""
    bullet_match = BULLET_PREFIX_REGEX.match(para.text)
    if bullet_match and not is_list_style:
        bullet_prefix = bullet_match.group(0)

    final_text = f"{bullet_prefix}{clean_tail}"
    
    if not para.runs:
        para.text = final_text
        return True

    # Single run paragraph: set text directly
    if len(para.runs) == 1:
        para.runs[0].text = final_text
        return True
        
    # Multi-run paragraph: update text runs while preserving date/location/tab runs
    updated = False
    for r in para.runs:
        r_str = r.text
        is_date_or_tab = bool(re.search(r"\b(20\d\d|19\d\d|Present|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Remote|Hybrid)\b", r_str, re.IGNORECASE)) or "\t" in r_str
        
        if not is_date_or_tab:
            if not updated:
                r.text = final_text
                updated = True
            else:
                r.text = ""
                
    if not updated and para.runs:
        para.runs[0].text = final_text
        
    return True

def create_docx(markdown_text: str, original_docx_bytes: Optional[bytes] = None, bullet_improvements: Optional[list] = None) -> BytesIO:
    """
    Converts markdown formatted resume into a Word (.docx) file.
    If original_docx_bytes is provided, modifies the candidate's ORIGINAL .docx file in-place,
    preserving 100% of original fonts, styles, centered titles, dates, line spacing, gaps, and margins.
    """
    if original_docx_bytes and len(original_docx_bytes) > 0:
        try:
            doc = docx.Document(BytesIO(original_docx_bytes))
            
            # Perform in-place paragraph text replacements on original docx DOM (checking main & table paragraphs)
            all_paragraphs = list(doc.paragraphs)
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        all_paragraphs.extend(cell.paragraphs)

            if bullet_improvements:
                for item in bullet_improvements:
                    if not isinstance(item, dict):
                        continue
                    orig = item.get("original", "").strip()
                    tail = item.get("tailored", "").strip()
                    if not orig or not tail or orig == tail:
                        continue
                        
                    for para in all_paragraphs:
                        if update_docx_paragraph_safely(para, orig, tail):
                            break

            output = BytesIO()
            doc.save(output)
            output.seek(0)
            return output
        except Exception as e:
            print(f"In-place docx modification failed: {e}. Falling back to template generation.")

    doc = docx.Document()
    
    # Page Margins (0.75 inch standard ATS margins)
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)
        
    lines = markdown_text.split("\n")
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
            
        is_bullet = (
            stripped.startswith("- ") 
            or stripped.startswith("* ") 
            or stripped.startswith("• ") 
            or stripped.startswith("▪ ") 
            or re.match(r"^[\s\t]*[•\-*o▪■\u2022\u25aa\u25a0]", stripped)
        )
        
        # Headers
        if stripped.startswith("# "):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(stripped[2:].strip())
            run.font.name = 'Calibri'
            run.font.size = Pt(18)
            run.font.bold = True
            run.font.color.rgb = RGBColor(30, 41, 59) # Dark Navy
        elif stripped.startswith("## "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(3)
            run = p.add_run(stripped[3:].strip())
            run.font.name = 'Calibri'
            run.font.size = Pt(13)
            run.font.bold = True
            run.font.color.rgb = RGBColor(15, 23, 42)
        elif stripped.startswith("### "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(2)
            run = p.add_run(stripped[4:].strip())
            run.font.name = 'Calibri'
            run.font.size = Pt(11)
            run.font.bold = True
            run.font.color.rgb = RGBColor(51, 65, 85)
        elif is_bullet:
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_after = Pt(2)
            text_content = re.sub(r"^[\s\t]*[•\-*o▪■\u2022\u25aa\u25a0]\s*", "", stripped).strip()
            # Handle inline bolding (**text**)
            parts = re.split(r'(\*\*.*?\*\*)', text_content)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    run = p.add_run(part[2:-2])
                    run.font.bold = True
                else:
                    run = p.add_run(part)
                run.font.name = 'Calibri'
                run.font.size = Pt(10.5)
        else:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(4)
            parts = re.split(r'(\*\*.*?\*\*)', stripped)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    run = p.add_run(part[2:-2])
                    run.font.bold = True
                else:
                    run = p.add_run(part)
                run.font.name = 'Calibri'
                run.font.size = Pt(10.5)
                
    output = BytesIO()
    doc.save(output)
    output.seek(0)
    return output

def create_pdf(markdown_text: str) -> BytesIO:
    """Converts markdown formatted resume into a clean ATS PDF file using ReportLab."""
    output = BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=letter,
        leftMargin=54, # 0.75 in
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'ResumeTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        alignment=1, # Center
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=8
    )
    
    h2_style = ParagraphStyle(
        'ResumeH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=10,
        spaceAfter=4
    )

    h3_style = ParagraphStyle(
        'ResumeH3',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceBefore=6,
        spaceAfter=2
    )

    body_style = ParagraphStyle(
        'ResumeBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=4
    )
    
    bullet_style = ParagraphStyle(
        'ResumeBullet',
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=2
    )
    
    story = []
    lines = markdown_text.split("\n")
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
            
        # Format inline bold tags for ReportLab (<b>text</b>)
        formatted_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', stripped)
        is_bullet = (
            stripped.startswith("- ") 
            or stripped.startswith("* ") 
            or stripped.startswith("• ") 
            or stripped.startswith("▪ ") 
            or re.match(r"^[\s\t]*[•\-*o▪■\u2022\u25aa\u25a0]", stripped)
        )
        
        if stripped.startswith("# "):
            text = formatted_line[2:].strip()
            story.append(Paragraph(text, title_style))
        elif stripped.startswith("## "):
            text = formatted_line[3:].strip()
            story.append(Paragraph(text.upper(), h2_style))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceBefore=1, spaceAfter=4))
        elif stripped.startswith("### "):
            text = formatted_line[4:].strip()
            story.append(Paragraph(text, h3_style))
        elif is_bullet:
            text_body = re.sub(r"^[\s\t]*[•\-*o▪■\u2022\u25aa\u25a0]\s*", "", formatted_line).strip()
            text = "&bull; " + text_body
            story.append(Paragraph(text, bullet_style))
        else:
            story.append(Paragraph(formatted_line, body_style))
            
    doc.build(story)
    output.seek(0)
    return output
