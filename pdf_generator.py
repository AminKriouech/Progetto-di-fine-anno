import io, base64
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import Frame, PageTemplate
from reportlab.platypus.flowables import Flowable
from reportlab.lib.utils import ImageReader


W, H = A4
ML, MR, MT, MB = 20*mm, 20*mm, 20*mm, 18*mm

# ── Colour constants ──────────────────────────────────────────────────────────
DARK       = colors.HexColor("#111111")
GRAY       = colors.HexColor("#555555")
LIGHTGRAY  = colors.HexColor("#888888")
RULE_GRAY  = colors.HexColor("#DDDDDD")
BLUE       = colors.HexColor("#185FA5")
BLUE_LIGHT = colors.HexColor("#E8F1FB")
NAVY       = colors.HexColor("#1a2332")
NAVY_TEXT  = colors.HexColor("#7eb8e8")
PURPLE     = colors.HexColor("#6B46C1")
PURPLE_BG  = colors.HexColor("#F5F0FF")
WHITE      = colors.white
BLACK      = colors.black


# ── Helpers ───────────────────────────────────────────────────────────────────
def safe(v, fallback=""):
    return v if v else fallback

def contact_line(d):
    parts = [d.get("email"), d.get("phone"), d.get("city"), d.get("link")]
    return "  ·  ".join(p for p in parts if p)

def _p(text, style):
    return Paragraph(text or "", style)

def _photo_reader(d):
    """Return an ImageReader from a base64 data URL, or None."""
    photo = d.get("photo")
    if not photo:
        return None
    try:
        # strip "data:image/...;base64,"
        if "," in photo:
            photo = photo.split(",", 1)[1]
        img_bytes = base64.b64decode(photo)
        return ImageReader(io.BytesIO(img_bytes))
    except Exception:
        return None


# ── CLASSIC TEMPLATE ──────────────────────────────────────────────────────────
def _classic(d):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=ML, rightMargin=MR,
                            topMargin=MT, bottomMargin=MB)

    s_name  = ParagraphStyle("n", fontName="Times-Bold",   fontSize=26, leading=30, textColor=DARK, spaceAfter=2)
    s_title = ParagraphStyle("t", fontName="Times-Italic", fontSize=13, leading=16, textColor=GRAY, spaceAfter=4)
    s_con   = ParagraphStyle("c", fontName="Times-Roman",  fontSize=9,  leading=12, textColor=LIGHTGRAY, spaceAfter=8)
    s_sec   = ParagraphStyle("s", fontName="Times-Bold",   fontSize=10, leading=13, textColor=DARK,
                              spaceBefore=10, spaceAfter=4, textTransform="uppercase", tracking=60)
    s_comp  = ParagraphStyle("co", fontName="Times-Bold",  fontSize=12, leading=15, textColor=DARK)
    s_role  = ParagraphStyle("r",  fontName="Times-Italic",fontSize=11, leading=14, textColor=GRAY)
    s_body  = ParagraphStyle("b",  fontName="Times-Roman", fontSize=10, leading=14, textColor=colors.HexColor("#444444"))
    s_summ  = ParagraphStyle("sm", fontName="Times-Italic",fontSize=11, leading=16, textColor=colors.HexColor("#444444"))

    story = []

    # Header: name + photo side by side
    photo_reader = _photo_reader(d)
    PHOTO_SIZE = 22*mm
    CONTENT_W  = W - ML - MR

    name_block = [
        _p(safe(d.get("name"), "Nome Cognome"), s_name),
    ]
    if d.get("title"):
        name_block.append(_p(d["title"], s_title))
    c = contact_line(d)
    if c:
        name_block.append(_p(c, s_con))

    if photo_reader:
        from reportlab.platypus import Image as RLImage
        photo_cell = RLImage(photo_reader, width=PHOTO_SIZE, height=PHOTO_SIZE,
                             kind="bound")
        photo_cell.hAlign = "RIGHT"
        header_table = Table(
            [[name_block, photo_cell]],
            colWidths=[CONTENT_W - PHOTO_SIZE - 6*mm, PHOTO_SIZE + 6*mm]
        )
        header_table.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("ALIGN",         (1, 0), (1, 0),   "RIGHT"),
        ]))
        story.append(header_table)
    else:
        for item in name_block:
            story.append(item)

    story.append(HRFlowable(width="100%", thickness=1.5, color=DARK, spaceAfter=6))

    if d.get("summary"):
        story.append(_p("Profilo", s_sec))
        story.append(HRFlowable(width="100%", thickness=0.4, color=RULE_GRAY, spaceAfter=5))
        story.append(_p(d["summary"], s_summ))
        story.append(Spacer(1, 6))

    if d.get("exp"):
        story.append(_p("Esperienza", s_sec))
        story.append(HRFlowable(width="100%", thickness=0.4, color=RULE_GRAY, spaceAfter=5))
        for e in d["exp"]:
            date_str = f"{e.get('start','')}–{e.get('end','')}"
            row = Table([[_p(e.get("company",""), s_comp), _p(date_str, ParagraphStyle("d", fontName="Times-Roman", fontSize=9, textColor=GRAY, alignment=TA_RIGHT))]],
                        colWidths=["80%","20%"])
            row.setStyle(TableStyle([("VALIGN",  (0,0),(-1,-1), "BOTTOM"),
                                     ("LEFTPADDING", (0,0),(-1,-1), 0),
                                     ("RIGHTPADDING",(0,0),(-1,-1), 0),
                                     ("TOPPADDING",  (0,0),(-1,-1), 0),
                                     ("BOTTOMPADDING",(0,0),(-1,-1),0)]))
            story.append(row)
            if e.get("role"):
                story.append(_p(e["role"], s_role))
            if e.get("desc"):
                story.append(_p(e["desc"], s_body))
            story.append(Spacer(1, 6))

    if d.get("edu"):
        story.append(_p("Formazione", s_sec))
        story.append(HRFlowable(width="100%", thickness=0.4, color=RULE_GRAY, spaceAfter=5))
        for e in d["edu"]:
            date_str = f"{e.get('start','')}–{e.get('end','')}"
            row = Table([[_p(e.get("inst",""), s_comp), _p(date_str, ParagraphStyle("dd", fontName="Times-Roman", fontSize=9, textColor=GRAY, alignment=TA_RIGHT))]],
                        colWidths=["80%","20%"])
            row.setStyle(TableStyle([("VALIGN",  (0,0),(-1,-1), "BOTTOM"),
                                     ("LEFTPADDING", (0,0),(-1,-1), 0),
                                     ("RIGHTPADDING",(0,0),(-1,-1), 0),
                                     ("TOPPADDING",  (0,0),(-1,-1), 0),
                                     ("BOTTOMPADDING",(0,0),(-1,-1),0)]))
            story.append(row)
            if e.get("degree"):
                story.append(_p(e["degree"], s_role))
            if e.get("notes"):
                story.append(_p(e["notes"], s_body))
            story.append(Spacer(1, 6))

    if d.get("skills"):
        story.append(_p("Competenze", s_sec))
        story.append(HRFlowable(width="100%", thickness=0.4, color=RULE_GRAY, spaceAfter=5))
        story.append(_p("  ·  ".join(d["skills"]), s_body))

    doc.build(story)
    buf.seek(0)
    return buf


# ── MODERN TEMPLATE (sidebar) ─────────────────────────────────────────────────
def _modern(d):
    buf = io.BytesIO()
    SIDE_W = 55*mm
    MAIN_X = SIDE_W + 8*mm
    MAIN_W = W - SIDE_W - 8*mm - MR

    c = rl_canvas.Canvas(buf, pagesize=A4)
    c.setFillColor(NAVY)
    c.rect(0, 0, SIDE_W, H, fill=1, stroke=0)

    y = H - MT

    # ── Sidebar content ──
    def sb_text(text, font, size, color, x_off=5*mm, align="left"):
        nonlocal y
        c.setFont(font, size)
        c.setFillColor(color)
        if align == "left":
            c.drawString(x_off, y, text)
        else:
            c.drawRightString(SIDE_W - 4*mm, y, text)
        y -= size * 1.5

    y = H - MT - 4*mm

    # Photo circle in sidebar
    photo_reader = _photo_reader(d)
    if photo_reader:
        PHOTO_D = 18*mm
        px = (SIDE_W - PHOTO_D) / 2
        py = y - PHOTO_D
        # Draw circular clip
        from reportlab.graphics.shapes import Circle
        c.saveState()
        p = c.beginPath()
        p.circle(px + PHOTO_D/2, py + PHOTO_D/2, PHOTO_D/2)
        c.clipPath(p, stroke=0)
        c.drawImage(photo_reader, px, py, PHOTO_D, PHOTO_D, preserveAspectRatio=True, mask="auto")
        c.restoreState()
        # circle border
        c.setStrokeColor(colors.HexColor("#2a4a6a"))
        c.setLineWidth(1)
        c.circle(px + PHOTO_D/2, py + PHOTO_D/2, PHOTO_D/2, stroke=1, fill=0)
        y = py - 8

    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(WHITE)
    name = safe(d.get("name"), "Nome Cognome")
    words = name.split()
    line = ""
    for w_txt in words:
        test = (line + " " + w_txt).strip()
        if c.stringWidth(test, "Helvetica-Bold", 14) < SIDE_W - 10*mm:
            line = test
        else:
            c.drawString(5*mm, y, line)
            y -= 18
            line = w_txt
    if line:
        c.drawString(5*mm, y, line)
        y -= 18

    if d.get("title"):
        c.setFont("Helvetica", 8)
        c.setFillColor(NAVY_TEXT)
        c.drawString(5*mm, y, d["title"].upper())
        y -= 14

    y -= 6
    c.setStrokeColor(colors.HexColor("#2a3f5a"))
    c.setLineWidth(0.5)
    c.line(5*mm, y, SIDE_W - 5*mm, y)
    y -= 10

    for label, key in [("Email", "email"), ("Tel", "phone"), ("Città", "city"), ("Web", "link")]:
        if d.get(key):
            c.setFont("Helvetica-Bold", 7)
            c.setFillColor(NAVY_TEXT)
            c.drawString(5*mm, y, label)
            y -= 10
            c.setFont("Helvetica", 7)
            c.setFillColor(colors.HexColor("#b0cce8"))
            val = d[key]
            if len(val) > 22:
                val = val[:22] + "…"
            c.drawString(5*mm, y, val)
            y -= 12

    if d.get("skills"):
        y -= 6
        c.line(5*mm, y, SIDE_W - 5*mm, y)
        y -= 12
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(NAVY_TEXT)
        c.drawString(5*mm, y, "COMPETENZE")
        y -= 12
        for sk in d["skills"]:
            if y < MB + 10*mm:
                break
            c.setFont("Helvetica", 7.5)
            c.setFillColor(colors.HexColor("#d0e8f8"))
            c.drawString(5*mm, y, f"• {sk}")
            y -= 10

    # ── Main content ──
    my = H - MT

    def section_title(title):
        nonlocal my
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(NAVY)
        c.drawString(MAIN_X, my, title)
        my -= 4
        c.setStrokeColor(BLUE)
        c.setLineWidth(1.5)
        c.line(MAIN_X, my, MAIN_X + MAIN_W, my)
        my -= 10

    def entry(title, subtitle, date, desc):
        nonlocal my
        if my < MB + 20*mm:
            return
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(DARK)
        c.drawString(MAIN_X, my, title)
        date_w = c.stringWidth(date, "Helvetica", 7) + 8
        c.setFillColor(BLUE_LIGHT)
        c.roundRect(MAIN_X + MAIN_W - date_w - 2, my - 2, date_w + 2, 11, 2, fill=1, stroke=0)
        c.setFont("Helvetica", 7)
        c.setFillColor(BLUE)
        c.drawString(MAIN_X + MAIN_W - date_w, my + 1, date)
        my -= 12
        if subtitle:
            c.setFont("Helvetica-Oblique", 9)
            c.setFillColor(GRAY)
            c.drawString(MAIN_X, my, subtitle)
            my -= 11
        if desc:
            c.setFont("Helvetica", 8.5)
            c.setFillColor(colors.HexColor("#444444"))
            words = desc.split()
            line = ""
            for w_txt in words:
                test = (line + " " + w_txt).strip()
                if c.stringWidth(test, "Helvetica", 8.5) < MAIN_W:
                    line = test
                else:
                    c.drawString(MAIN_X, my, line)
                    my -= 11
                    line = w_txt
                    if my < MB + 10*mm:
                        break
            if line and my > MB + 10*mm:
                c.drawString(MAIN_X, my, line)
                my -= 11
        my -= 6

    if d.get("summary"):
        section_title("Profilo")
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColor(GRAY)
        words = d["summary"].split()
        line = ""
        for w_txt in words:
            test = (line + " " + w_txt).strip()
            if c.stringWidth(test, "Helvetica-Oblique", 9) < MAIN_W:
                line = test
            else:
                c.drawString(MAIN_X, my, line)
                my -= 11
                line = w_txt
        if line:
            c.drawString(MAIN_X, my, line)
            my -= 14

    if d.get("exp"):
        section_title("Esperienza")
        for e in d["exp"]:
            entry(e.get("company",""), e.get("role",""),
                  f"{e.get('start','')}–{e.get('end','')}", e.get("desc",""))

    if d.get("edu"):
        section_title("Formazione")
        for e in d["edu"]:
            entry(e.get("inst",""), e.get("degree",""),
                  f"{e.get('start','')}–{e.get('end','')}", e.get("notes",""))

    c.save()
    buf.seek(0)
    return buf


# ── MINIMAL TEMPLATE ──────────────────────────────────────────────────────────
def _minimal(d):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=ML+6*mm, rightMargin=MR+6*mm,
                            topMargin=MT+6*mm, bottomMargin=MB)

    DATE_W  = 35*mm
    BODY_W  = W - (ML+6*mm) - (MR+6*mm) - DATE_W - 4*mm

    s_name  = ParagraphStyle("n", fontName="Helvetica",      fontSize=28, leading=32, textColor=DARK, fontWeight=300)
    s_title = ParagraphStyle("t", fontName="Helvetica",      fontSize=11, leading=14, textColor=LIGHTGRAY, spaceAfter=12)
    s_sec   = ParagraphStyle("s", fontName="Helvetica",      fontSize=8,  leading=11, textColor=LIGHTGRAY,
                              spaceBefore=14, spaceAfter=6, tracking=120)
    s_comp  = ParagraphStyle("c", fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=DARK)
    s_sub   = ParagraphStyle("sb",fontName="Helvetica",      fontSize=10, leading=13, textColor=LIGHTGRAY)
    s_body  = ParagraphStyle("b", fontName="Helvetica",      fontSize=9,  leading=13, textColor=GRAY)
    s_date  = ParagraphStyle("d", fontName="Helvetica",      fontSize=9,  leading=13, textColor=LIGHTGRAY)
    s_summ  = ParagraphStyle("sm",fontName="Helvetica",      fontSize=10, leading=15, textColor=GRAY)
    s_con   = ParagraphStyle("co",fontName="Helvetica",      fontSize=9,  leading=13, textColor=LIGHTGRAY, alignment=TA_RIGHT)

    story = []

    photo_reader = _photo_reader(d)
    PHOTO_SIZE   = 20*mm
    CONTENT_W    = W - (ML+6*mm) - (MR+6*mm)

    name_col = [_p(safe(d.get("name"), "Nome Cognome"), s_name)]
    if d.get("title"):
        name_col.append(_p(d["title"], s_title))

    contact_col = _p(contact_line(d).replace("  ·  ", "\n"), s_con)

    if photo_reader:
        from reportlab.platypus import Image as RLImage
        photo_img = RLImage(photo_reader, width=PHOTO_SIZE, height=PHOTO_SIZE, kind="bound")
        photo_img.hAlign = "RIGHT"
        header = Table(
            [[name_col, contact_col, photo_img]],
            colWidths=[CONTENT_W - 70*mm - PHOTO_SIZE, 70*mm - 6*mm, PHOTO_SIZE + 6*mm]
        )
    else:
        header = Table(
            [[name_col, contact_col]],
            colWidths=["65%", "35%"]
        )

    header.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "BOTTOM"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header)
    if d.get("title") and not photo_reader:
        pass  # already in name_col
    story.append(HRFlowable(width="100%", thickness=0.5, color=RULE_GRAY, spaceAfter=8))

    if d.get("summary"):
        row = Table([[_p("Profilo".upper(), s_sec), _p(d["summary"], s_summ)]],
                    colWidths=[DATE_W, BODY_W])
        row.setStyle(TableStyle([(("VALIGN"),(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),0),
                                  ("RIGHTPADDING",(0,0),(-1,-1),0),("TOPPADDING",(0,0),(-1,-1),0),
                                  ("BOTTOMPADDING",(0,0),(-1,-1),0)]))
        story.append(row)
        story.append(Spacer(1, 8))

    s_empty = ParagraphStyle("em", fontName="Helvetica", fontSize=1)

    def section(title, items, name_key, sub_key, date_keys, desc_key):
        story.append(HRFlowable(width="100%", thickness=0.3, color=RULE_GRAY, spaceAfter=4))
        for i, e in enumerate(items):
            date_str = "–".join(str(e.get(k,"")) for k in date_keys if e.get(k))
            content = [_p(e.get(name_key,""), s_comp)]
            if e.get(sub_key):  content.append(_p(e[sub_key], s_sub))
            if e.get(desc_key): content.append(_p(e[desc_key], s_body))
            tbl = Table([[_p(title.upper() if i==0 else "", s_sec),
                          _p(date_str, s_date),
                          content[0]]],
                        colWidths=[DATE_W, DATE_W, BODY_W - DATE_W])
            tbl.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),
                                      ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
                                      ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0)]))
            story.append(tbl)
            for c2 in content[1:]:
                t2 = Table([[_p("", s_empty), _p("", s_empty), c2]],
                           colWidths=[DATE_W, DATE_W, BODY_W - DATE_W])
                t2.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),
                                         ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
                                         ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0)]))
                story.append(t2)
            story.append(Spacer(1, 6))

    if d.get("exp"):
        section("Esperienza", d["exp"], "company", "role", ["start","end"], "desc")
    if d.get("edu"):
        section("Formazione", d["edu"], "inst", "degree", ["start","end"], "notes")
    if d.get("skills"):
        story.append(HRFlowable(width="100%", thickness=0.3, color=RULE_GRAY, spaceAfter=4))
        sk_row = Table([[_p("Competenze".upper(), s_sec),
                         _p("  ·  ".join(d["skills"]), s_body)]],
                       colWidths=[DATE_W, BODY_W])
        sk_row.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),
                                     ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
                                     ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0)]))
        story.append(sk_row)

    doc.build(story)
    buf.seek(0)
    return buf


# ── CREATIVE TEMPLATE ─────────────────────────────────────────────────────────
def _creative(d):
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)

    HEADER_H = 52*mm
    RIGHT_W  = 60*mm
    MAIN_X   = ML
    MAIN_W   = W - ML - MR - RIGHT_W - 6*mm
    RIGHT_X  = W - MR - RIGHT_W

    # Purple header
    c.setFillColor(PURPLE)
    c.rect(0, H - HEADER_H, W, HEADER_H, fill=1, stroke=0)

    # Photo in header (circle, top-right area)
    photo_reader = _photo_reader(d)
    name_x = ML
    if photo_reader:
        PHOTO_D = 20*mm
        px = W - MR - PHOTO_D - 4*mm
        py = H - HEADER_H + (HEADER_H - PHOTO_D) / 2
        c.saveState()
        p = c.beginPath()
        p.circle(px + PHOTO_D/2, py + PHOTO_D/2, PHOTO_D/2)
        c.clipPath(p, stroke=0)
        c.drawImage(photo_reader, px, py, PHOTO_D, PHOTO_D,
                    preserveAspectRatio=True, mask="auto")
        c.restoreState()
        c.setStrokeColor(colors.HexColor("#9B6FE0"))
        c.setLineWidth(1)
        c.circle(px + PHOTO_D/2, py + PHOTO_D/2, PHOTO_D/2, stroke=1, fill=0)

    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(WHITE)
    c.drawString(name_x, H - MT - 6*mm, safe(d.get("name"), "Nome Cognome"))

    if d.get("title"):
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor("#c4aaee"))
        c.drawString(name_x, H - MT - 16*mm, d["title"])

    ct = contact_line(d)
    if ct:
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor("#d4baf4"))
        c.drawString(name_x, H - MT - 26*mm, ct)

    # Right panel background
    c.setFillColor(PURPLE_BG)
    c.rect(RIGHT_X - 4*mm, 0, RIGHT_W + 4*mm + MR, H - HEADER_H, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#E8DEFF"))
    c.setLineWidth(0.5)
    c.line(RIGHT_X - 4*mm, 0, RIGHT_X - 4*mm, H - HEADER_H)

    my = H - HEADER_H - 10*mm
    ry = H - HEADER_H - 10*mm

    def main_section(title):
        nonlocal my
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(PURPLE)
        c.drawString(MAIN_X, my, title.upper())
        my -= 4
        c.setStrokeColor(PURPLE)
        c.setLineWidth(1)
        c.line(MAIN_X, my, MAIN_X + MAIN_W, my)
        my -= 10

    def main_entry(title, subtitle, date, desc):
        nonlocal my
        if my < MB + 15*mm:
            return
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(DARK)
        c.drawString(MAIN_X, my, title)
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(PURPLE)
        c.drawRightString(MAIN_X + MAIN_W, my, date)
        my -= 12
        if subtitle:
            c.setFont("Helvetica-Oblique", 9)
            c.setFillColor(GRAY)
            c.drawString(MAIN_X, my, subtitle)
            my -= 11
        if desc:
            c.setFont("Helvetica", 8.5)
            c.setFillColor(colors.HexColor("#444444"))
            words = desc.split()
            line = ""
            for w_txt in words:
                test = (line + " " + w_txt).strip()
                if c.stringWidth(test, "Helvetica", 8.5) < MAIN_W:
                    line = test
                else:
                    c.drawString(MAIN_X, my, line)
                    my -= 11
                    line = w_txt
                    if my < MB + 10*mm:
                        break
            if line and my > MB + 10*mm:
                c.drawString(MAIN_X, my, line)
                my -= 11
        my -= 8

    def right_section(title):
        nonlocal ry
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(LIGHTGRAY)
        c.drawString(RIGHT_X, ry, title.upper())
        ry -= 4
        c.setStrokeColor(colors.HexColor("#D4BBEE"))
        c.setLineWidth(0.5)
        c.line(RIGHT_X, ry, RIGHT_X + RIGHT_W, ry)
        ry -= 10

    if d.get("summary"):
        main_section("Profilo")
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColor(GRAY)
        words = d["summary"].split()
        line = ""
        for w_txt in words:
            test = (line + " " + w_txt).strip()
            if c.stringWidth(test, "Helvetica-Oblique", 9) < MAIN_W:
                line = test
            else:
                c.drawString(MAIN_X, my, line)
                my -= 12
                line = w_txt
        if line:
            c.drawString(MAIN_X, my, line)
            my -= 16

    if d.get("exp"):
        main_section("Esperienza")
        for e in d["exp"]:
            main_entry(e.get("company",""), e.get("role",""),
                       f"{e.get('start','')}–{e.get('end','')}", e.get("desc",""))

    if d.get("edu"):
        main_section("Formazione")
        for e in d["edu"]:
            main_entry(e.get("inst",""), e.get("degree",""),
                       f"{e.get('start','')}–{e.get('end','')}", e.get("notes",""))

    if d.get("skills"):
        right_section("Competenze")
        for sk in d["skills"]:
            if ry < MB + 10*mm:
                break
            pill_w = c.stringWidth(sk, "Helvetica", 8) + 12
            if pill_w > RIGHT_W:
                pill_w = RIGHT_W
            c.setFillColor(colors.HexColor("#E8DEFF"))
            c.roundRect(RIGHT_X, ry - 2, pill_w, 12, 3, fill=1, stroke=0)
            c.setFont("Helvetica", 8)
            c.setFillColor(PURPLE)
            c.drawString(RIGHT_X + 5, ry + 1.5, sk[:20])
            ry -= 16

    c.save()
    buf.seek(0)
    return buf


# ── Public entry point ────────────────────────────────────────────────────────
def build_pdf(data, template):
    builders = {
        "classic":  _classic,
        "modern":   _modern,
        "minimal":  _minimal,
        "creative": _creative,
    }
    fn = builders.get(template, _classic)
    return fn(data)
