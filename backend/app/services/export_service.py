import os
import re
import tempfile
import traceback
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.note import NoteFile, NoteEntry


async def export_all_files(
    db: AsyncSession,
    project_id: str,
    fmt: str,
    output_dir: str | None = None,
) -> str:
    """Export all files in project to specified format. Returns output path."""
    result = await db.execute(
        select(NoteFile).where(NoteFile.project_id == project_id)
    )
    files = list(result.scalars().all())

    if not files:
        raise ValueError("No files to export")

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="note_export_")

    exporter = _get_exporter(fmt)
    return await exporter(db, files, output_dir)


async def export_single_file(
    db: AsyncSession,
    file_id: str,
    fmt: str,
) -> str:
    """Export a single file. Returns output path."""
    result = await db.execute(select(NoteFile).where(NoteFile.id == file_id))
    nf = result.scalar_one_or_none()
    if not nf:
        raise ValueError("File not found")

    result2 = await db.execute(
        select(NoteEntry)
        .where(NoteEntry.note_file_id == file_id)
        .order_by(NoteEntry.sort_order)
    )
    entries = list(result2.scalars().all())

    output_dir = tempfile.mkdtemp(prefix="note_export_")
    output_path = os.path.join(output_dir, nf.filename)

    if fmt == "md":
        return _export_single_md(nf, entries, output_dir)
    elif fmt == "html":
        return _export_single_html(nf, entries, output_dir)
    elif fmt == "txt":
        return _export_single_txt(nf, entries, output_dir)
    elif fmt == "docx":
        return await _export_single_docx(nf, entries, output_dir)
    elif fmt == "pdf":
        return await _export_single_pdf(nf, entries, output_dir)
    else:
        raise ValueError(f"Unsupported format: {fmt}")


def _get_exporter(fmt: str):
    mapping = {
        "md": _export_all_md,
        "html": _export_all_html,
        "txt": _export_all_txt,
        "docx": _export_all_docx,
        "pdf": _export_all_pdf,
    }
    if fmt not in mapping:
        raise ValueError(f"Unsupported format: {fmt}")
    return mapping[fmt]


def _strip_html_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def _format_entry_for_export(entry: NoteEntry, fmt: str = "md") -> str:
    """Format a single entry for export."""
    content = entry.highlighted_content or entry.content

    if fmt == "txt":
        return _strip_html_tags(content) + "\n"

    if fmt == "md":
        # Convert HTML highlights to markdown
        text = content
        text = re.sub(r'<span class="hl-red">(.*?)</span>', r"**\1** 🔴", text)
        text = re.sub(r'<span class="hl-blue">(.*?)</span>', r"**\1** 🔵", text)
        text = re.sub(r'<span class="hl-green">(.*?)</span>', r"**\1** 🟢", text)
        text = re.sub(r'<span class="hl-orange">(.*?)</span>', r"**\1** 🟠", text)
        text = re.sub(r'<span class="hl-bold">(.*?)</span>', r"**\1**", text)
        text = re.sub(r"<strong>(.*?)</strong>", r"**\1**", text)
        text = re.sub(r"<br\s*/?>", "\n", text)
        return text + "\n"

    return content


async def _export_all_md(db, files, output_dir) -> str:
    for nf in files:
        result = await db.execute(
            select(NoteEntry)
            .where(NoteEntry.note_file_id == nf.id)
            .order_by(NoteEntry.sort_order)
        )
        entries = list(result.scalars().all())
        _export_single_md(nf, entries, output_dir)
    return output_dir


def _export_single_md(nf, entries, output_dir) -> str:
    filename = os.path.splitext(nf.filename)[0] + ".md"
    output_path = os.path.join(output_dir, filename)

    lines = [f"# {nf.filename}", ""]
    if nf.keywords:
        lines.append(f"**关键词**: {nf.keywords}")
    if nf.summary:
        lines.append(f"> {nf.summary}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for entry in entries:
        lines.append(_format_entry_for_export(entry, "md"))
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return output_path


async def _export_all_html(db, files, output_dir) -> str:
    all_html_parts = []
    toc = ["<nav><h2>目录</h2><ul>"]

    for i, nf in enumerate(files):
        result = await db.execute(
            select(NoteEntry)
            .where(NoteEntry.note_file_id == nf.id)
            .order_by(NoteEntry.sort_order)
        )
        entries = list(result.scalars().all())

        file_id = f"file_{i}"
        toc.append(f'<li><a href="#{file_id}">{nf.filename}</a></li>')

        parts = [f'<section id="{file_id}"><h2>{nf.filename}</h2>']
        if nf.keywords:
            parts.append(f'<p class="keywords">关键词: {nf.keywords}</p>')
        if nf.summary:
            parts.append(f'<blockquote>{nf.summary}</blockquote>')

        for entry in entries:
            content = entry.highlighted_content or entry.content
            parts.append(f'<div class="entry importance-{entry.importance}" style="border-left: 3px solid {_color_to_css(entry.color)};">{content}</div>')

        parts.append("</section>")
        all_html_parts.append("\n".join(parts))

    toc.append("</ul></nav>")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>导出笔记</title>
<style>
body {{ font-family: 'Microsoft YaHei', sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.8; }}
nav {{ background: #f5f5f5; padding: 15px; border-radius: 8px; margin-bottom: 30px; }}
nav ul {{ list-style: none; padding: 0; }}
nav li {{ margin: 5px 0; }}
section {{ margin-bottom: 40px; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; }}
.keywords {{ color: #666; font-size: 0.9em; }}
.entry {{ padding: 10px; margin: 8px 0; background: #fafafa; border-radius: 4px; }}
.hl-red {{ background-color: #ffe0e0; color: #c00; font-weight: bold; }}
.hl-blue {{ background-color: #e0e0ff; color: #0066cc; font-weight: bold; }}
.hl-green {{ background-color: #e0ffe0; color: #006600; font-weight: bold; }}
.hl-orange {{ background-color: #fff0d0; color: #c60; font-weight: bold; }}
.hl-bold {{ font-weight: bold; }}
blockquote {{ border-left: 4px solid #ccc; padding-left: 15px; color: #555; }}
</style>
</head>
<body>
{"".join(toc)}
{"".join(all_html_parts)}
</body>
</html>"""

    output_path = os.path.join(output_dir, "export.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_dir


def _export_single_html(nf, entries, output_dir) -> str:
    filename = os.path.splitext(nf.filename)[0] + ".html"
    output_path = os.path.join(output_dir, filename)

    parts = [f"<h1>{nf.filename}</h1>"]
    if nf.keywords:
        parts.append(f'<p class="keywords">关键词: {nf.keywords}</p>')
    if nf.summary:
        parts.append(f"<blockquote>{nf.summary}</blockquote>")

    for entry in entries:
        content = entry.highlighted_content or entry.content
        parts.append(f'<div class="entry" style="border-left-color:{_color_to_css(entry.color)}">{content}</div>')

    html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{nf.filename}</title>
<style>
body {{ font-family: 'Microsoft YaHei', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.8; }}
.entry {{ padding: 10px; margin: 8px 0; border-left: 3px solid #ccc; background: #fafafa; border-radius: 4px; }}
.hl-red {{ background-color: #ffe0e0; color: #c00; font-weight: bold; }}
.hl-blue {{ background-color: #e0e0ff; color: #0066cc; font-weight: bold; }}
.hl-green {{ background-color: #e0ffe0; color: #006600; font-weight: bold; }}
.hl-orange {{ background-color: #fff0d0; color: #c60; font-weight: bold; }}
.hl-bold {{ font-weight: bold; }}
</style></head><body>
{"".join(parts)}
</body></html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path


async def _export_all_txt(db, files, output_dir) -> str:
    for nf in files:
        result = await db.execute(
            select(NoteEntry)
            .where(NoteEntry.note_file_id == nf.id)
            .order_by(NoteEntry.sort_order)
        )
        entries = list(result.scalars().all())
        _export_single_txt(nf, entries, output_dir)
    return output_dir


def _export_single_txt(nf, entries, output_dir) -> str:
    output_path = os.path.join(output_dir, nf.filename)
    lines = [f"{'=' * 50}", f"文件: {nf.filename}", f"{'=' * 50}", ""]
    if nf.keywords:
        lines.append(f"关键词: {nf.keywords}")
    if nf.summary:
        lines.append(f"摘要: {nf.summary}")
    lines.append("")

    for entry in entries:
        lines.append(_format_entry_for_export(entry, "txt"))
        lines.append("-" * 30)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return output_path


async def _export_all_docx(db, files, output_dir) -> str:
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches

    doc = Document()
    style = doc.styles["Normal"]
    style.font.size = Pt(11)
    style.font.name = "SimSun"
    from docx.oxml.ns import qn
    style.element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')

    for nf in files:
        doc.add_heading(nf.filename, level=1)
        if nf.keywords:
            p = doc.add_paragraph()
            run = p.add_run(f"关键词: {nf.keywords}")
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(128, 128, 128)
            run.font.name = "SimSun"
            run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
        if nf.summary:
            p = doc.add_paragraph(f"> {nf.summary}")

        result = await db.execute(
            select(NoteEntry)
            .where(NoteEntry.note_file_id == nf.id)
            .order_by(NoteEntry.sort_order)
        )
        entries = list(result.scalars().all())

        for entry in entries:
            p = doc.add_paragraph()
            text = _strip_html_tags(entry.content)
            run = p.add_run(text)
            run.font.name = "SimSun"
            run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
            run.font.size = Pt(11)
            if entry.importance == "high":
                run.font.bold = True
                run.font.color.rgb = RGBColor(204, 0, 0)
            elif entry.importance == "medium":
                run.font.color.rgb = RGBColor(0, 102, 204)
            else:
                run.font.color.rgb = RGBColor(80, 80, 80)

    output_path = os.path.join(output_dir, "export.docx")
    doc.save(output_path)
    return output_dir


async def _export_single_docx(nf, entries, output_dir) -> str:
    from docx import Document
    from docx.shared import Pt, RGBColor
    from docx.oxml.ns import qn

    output_path = os.path.join(output_dir, os.path.splitext(nf.filename)[0] + ".docx")
    doc = Document()
    style = doc.styles["Normal"]
    style.font.size = Pt(11)
    style.font.name = "SimSun"
    style.element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')

    doc.add_heading(nf.filename, level=1)
    if nf.keywords:
        p = doc.add_paragraph()
        run = p.add_run(f"关键词: {nf.keywords}")
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(128, 128, 128)
        run.font.name = "SimSun"
        run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
    if nf.summary:
        doc.add_paragraph(f"> {nf.summary}")

    for entry in entries:
        p = doc.add_paragraph()
        text = _strip_html_tags(entry.content)
        run = p.add_run(text)
        run.font.name = "SimSun"
        run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
        run.font.size = Pt(11)
        if entry.importance == "high":
            run.font.bold = True
            run.font.color.rgb = RGBColor(204, 0, 0)
        elif entry.importance == "medium":
            run.font.color.rgb = RGBColor(0, 102, 204)

    doc.save(output_path)
    return output_path


def _find_chinese_font() -> str:
    """Find a Chinese-capable TTF font on the system."""
    candidates = [
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return ""


def _pdf_write_text(pdf, text: str, font: str, size: int = 11, color: tuple = (0, 0, 0), bold: bool = False):
    """Write a line of Chinese text to PDF with word wrapping."""
    pdf.set_font(family=font, size=size)
    style = "B" if bold else ""
    if style:
        pdf.set_font(family=font, size=size, style=style)
    pdf.set_text_color(*color)
    try:
        pdf.multi_cell(w=0, h=size * 1.2, text=text, align="L")
    except Exception:
        pdf.multi_cell(w=0, h=size * 1.2, text=text.encode("utf-8", errors="replace").decode("utf-8"), align="L")


async def _export_all_pdf(db, files, output_dir) -> str:
    output_path = os.path.join(output_dir, "export.pdf")
    try:
        font_path = _find_chinese_font()
        if not font_path:
            raise RuntimeError("未找到中文字体文件，请使用 HTML 导出")
        try:
            from fpdf import FPDF
        except ImportError:
            raise RuntimeError("缺少 fpdf2 库，请运行: pip install fpdf2")
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_font("CJK", "", font_path, uni=True)
        pdf.add_font("CJK", "B", font_path, uni=True)

        for nf in files:
            pdf.add_page()
            # Title
            pdf.set_font("CJK", "B", 16)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 12, nf.filename, ln=True)
            pdf.ln(4)

            # Keywords
            if nf.keywords:
                pdf.set_font("CJK", "", 9)
                pdf.set_text_color(128, 128, 128)
                pdf.cell(0, 8, f"关键词: {nf.keywords}", ln=True)

            # Summary
            if nf.summary:
                pdf.set_font("CJK", "", 10)
                pdf.set_text_color(100, 100, 100)
                pdf.multi_cell(0, 7, nf.summary)
            pdf.ln(4)

            # Entries
            result = await db.execute(
                select(NoteEntry).where(NoteEntry.note_file_id == nf.id).order_by(NoteEntry.sort_order)
            )
            entries = list(result.scalars().all())

            for entry in entries:
                text = _strip_html_tags(entry.content)
                color = (60, 60, 60)
                bold = False
                if entry.importance == "high":
                    color, bold = (180, 0, 0), True
                elif entry.importance == "medium":
                    color = (0, 80, 160)
                _pdf_write_text(pdf, text, "CJK", size=10, color=color, bold=bold)
                pdf.ln(3)

        pdf.output(output_path)
    except Exception as e:
        traceback.print_exc()
        raise RuntimeError(f"PDF生成失败: {e}")
    return output_dir


async def _export_single_pdf(nf, entries, output_dir) -> str:
    output_path = os.path.join(output_dir, os.path.splitext(nf.filename)[0] + ".pdf")
    try:
        font_path = _find_chinese_font()
        if not font_path:
            raise RuntimeError("未找到中文字体文件，请使用 HTML 导出")
        try:
            from fpdf import FPDF
        except ImportError:
            raise RuntimeError("缺少 fpdf2 库，请运行: pip install fpdf2")
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_font("CJK", "", font_path, uni=True)
        pdf.add_font("CJK", "B", font_path, uni=True)

        pdf.add_page()
        pdf.set_font("CJK", "B", 16)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 12, nf.filename, ln=True)
        pdf.ln(4)

        if nf.keywords:
            pdf.set_font("CJK", "", 9)
            pdf.set_text_color(128, 128, 128)
            pdf.cell(0, 8, f"关键词: {nf.keywords}", ln=True)
        if nf.summary:
            pdf.set_font("CJK", "", 10)
            pdf.set_text_color(100, 100, 100)
            pdf.multi_cell(0, 7, nf.summary)
        pdf.ln(4)

        for entry in entries:
            text = _strip_html_tags(entry.content)
            color = (60, 60, 60)
            bold = False
            if entry.importance == "high":
                color, bold = (180, 0, 0), True
            elif entry.importance == "medium":
                color = (0, 80, 160)
            _pdf_write_text(pdf, text, "CJK", size=10, color=color, bold=bold)
            pdf.ln(3)

        pdf.output(output_path)
    except Exception as e:
        traceback.print_exc()
        raise RuntimeError(f"PDF生成失败: {e}")
    return output_path


def _color_to_css(color: str | None) -> str:
    mapping = {
        "red": "#c00",
        "blue": "#0066cc",
        "green": "#006600",
        "yellow": "#e6c300",
        "orange": "#c60",
        "purple": "#8040c0",
    }
    return mapping.get(color or "", "#ccc")
