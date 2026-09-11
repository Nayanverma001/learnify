import os
import platform
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


# ----------------------------------------------------------------------
# Cross-Platform TrueType Font Resolution
# ----------------------------------------------------------------------

def _resolve_font_path(bold=False, mono=False):
    system = platform.system().lower()
    candidates = []

    if 'windows' in system:
        font_dir = Path(os.environ.get('WINDIR', 'C:\\Windows')) / 'Fonts'
        if mono:
            candidates.extend([font_dir / 'consola.ttf', font_dir / 'cour.ttf'])
        elif bold:
            candidates.extend([
                font_dir / 'segoeuib.ttf',
                font_dir / 'arialbd.ttf',
                font_dir / 'calibrib.ttf',
                font_dir / 'tahomabd.ttf',
            ])
        else:
            candidates.extend([
                font_dir / 'segoeui.ttf',
                font_dir / 'arial.ttf',
                font_dir / 'calibri.ttf',
                font_dir / 'tahoma.ttf',
            ])
    elif 'darwin' in system:
        if mono:
            candidates.extend([Path('/System/Library/Fonts/Monaco.ttf'), Path('/Library/Fonts/Courier New.ttf')])
        elif bold:
            candidates.extend([Path('/System/Library/Fonts/SFNSBold.ttf'), Path('/Library/Fonts/Arial Bold.ttf')])
        else:
            candidates.extend([Path('/System/Library/Fonts/SFNSText.ttf'), Path('/Library/Fonts/Arial.ttf')])
    else:
        if mono:
            candidates.extend([
                Path('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'),
                Path('/usr/share/fonts/truetype/freefont/FreeMono.ttf'),
            ])
        elif bold:
            candidates.extend([
                Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
                Path('/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'),
                Path('/usr/share/fonts/truetype/freefont/FreeSansBold.ttf'),
            ])
        else:
            candidates.extend([
                Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
                Path('/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'),
                Path('/usr/share/fonts/truetype/freefont/FreeSans.ttf'),
            ])

    for p in candidates:
        if p.exists():
            return str(p)
    return None


def _get_font(size, bold=False, mono=False):
    path = _resolve_font_path(bold=bold, mono=mono)
    if path:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _fonts():
    return {
        'display': _get_font(34, bold=True),
        'title': _get_font(26, bold=True),
        'sub': _get_font(20, bold=True),
        'body': _get_font(18, bold=False),
        'body_bold': _get_font(18, bold=True),
        'small': _get_font(14, bold=False),
        'small_bold': _get_font(14, bold=True),
        'code': _get_font(16, mono=True),
    }


BG_DARK = (11, 14, 28)
PANEL_BG = (22, 26, 52)
PANEL_BORDER = (55, 62, 105)
GLOW_PURPLE = (109, 93, 252)
GLOW_CYAN = (0, 225, 255)
GLOW_EMERALD = (52, 211, 153)
CARD_BG = (30, 35, 70)
CARD_BORDER = (75, 82, 135)
TEXT_WHITE = (255, 255, 255)
TEXT_MUTED = (195, 192, 220)
TEXT_HIGHLIGHT = (165, 155, 255)


def _draw_gradient_bg(image):
    draw = ImageDraw.Draw(image)
    w, h = image.size
    for y in range(h):
        ratio = y / h
        r = int(10 + (22 - 10) * ratio)
        g = int(13 + (26 - 13) * ratio)
        b = int(28 + (54 - 28) * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    for radius, alpha_col in [
        (280, (45, 35, 95)),
        (180, (65, 48, 135)),
        (90, (85, 65, 175)),
    ]:
        draw.ellipse((-80, -80, radius * 2 - 80, radius * 2 - 80), fill=alpha_col)

    for radius, alpha_col in [
        (220, (15, 45, 75)),
        (130, (20, 65, 105)),
    ]:
        draw.ellipse((w - radius * 2 + 80, h - radius * 2 + 80, w + 80, h + 80), fill=alpha_col)


def _draw_card(draw, x, y, w, h, radius=16, fill=CARD_BG, outline=CARD_BORDER, shadow=True):
    if shadow:
        draw.rounded_rectangle((x + 2, y + 4, x + w + 2, y + h + 4), radius=radius, fill=(8, 10, 20))
    draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=fill, outline=outline, width=2)


def _wrap_text(text, width=38):
    return textwrap.fill(str(text or '').strip(), width=width)


def _draw_flow(draw, data, area, fonts):
    x, y, w, h = area
    raw_nodes = data.get('nodes', [])
    if not raw_nodes:
        raw_nodes = ['Start', 'Process Step', 'Decision / Check', 'Output']

    nodes = []
    for item in raw_nodes[:8]:
        if isinstance(item, dict):
            nodes.append(str(item.get('label') or item.get('name') or item.get('id') or 'Step'))
        else:
            nodes.append(str(item))

    num_nodes = len(nodes)
    if num_nodes == 0:
        return

    if num_nodes <= 4:
        gap = 20
        box_w = min(150, (w - gap * (num_nodes - 1)) // num_nodes)
        box_h = 74
        start_x = x + (w - (box_w * num_nodes + gap * (num_nodes - 1))) // 2
        cy = y + (h - box_h) // 2

        for i, label in enumerate(nodes):
            bx = start_x + i * (box_w + gap)
            _draw_card(draw, bx, cy, box_w, box_h, radius=12, fill=CARD_BG, outline=GLOW_PURPLE)
            draw.text((bx + 10, cy + 8), f'0{i+1}', font=fonts['small_bold'], fill=GLOW_CYAN)
            wrapped = textwrap.shorten(label, width=22, placeholder='…')
            draw.text((bx + 12, cy + 34), wrapped, font=fonts['small_bold'], fill=TEXT_WHITE)

            if i < num_nodes - 1:
                ax_start = bx + box_w + 3
                ax_end = bx + box_w + gap - 5
                mid_y = cy + box_h // 2
                draw.line([(ax_start, mid_y), (ax_end, mid_y)], fill=GLOW_CYAN, width=3)
                draw.polygon([(ax_end, mid_y), (ax_end - 6, mid_y - 4), (ax_end - 6, mid_y + 4)], fill=GLOW_CYAN)
    else:
        row1 = nodes[: (num_nodes + 1) // 2]
        row2 = nodes[(num_nodes + 1) // 2 :]
        box_w = min(150, (w - 20 * (len(row1) - 1)) // len(row1))
        box_h = 64
        y1 = y + 20
        y2 = y + h - box_h - 20

        start_x1 = x + (w - (box_w * len(row1) + 20 * (len(row1) - 1))) // 2
        for i, label in enumerate(row1):
            bx = start_x1 + i * (box_w + 20)
            _draw_card(draw, bx, y1, box_w, box_h, radius=10, fill=CARD_BG, outline=GLOW_PURPLE)
            draw.text((bx + 8, y1 + 6), f'0{i+1}', font=fonts['small'], fill=GLOW_CYAN)
            draw.text((bx + 10, y1 + 28), textwrap.shorten(label, width=20, placeholder='…'), font=fonts['small_bold'], fill=TEXT_WHITE)
            if i < len(row1) - 1:
                ax = bx + box_w + 3
                draw.line([(ax, y1 + box_h // 2), (ax + 14, y1 + box_h // 2)], fill=GLOW_CYAN, width=3)
                draw.polygon([(ax + 14, y1 + box_h // 2), (ax + 8, y1 + box_h // 2 - 4), (ax + 8, y1 + box_h // 2 + 4)], fill=GLOW_CYAN)

        r1_last_x = start_x1 + (len(row1) - 1) * (box_w + 20) + box_w // 2
        draw.line([(r1_last_x, y1 + box_h), (r1_last_x, y2)], fill=GLOW_PURPLE, width=3)
        draw.polygon([(r1_last_x, y2), (r1_last_x - 4, y2 - 6), (r1_last_x + 4, y2 - 6)], fill=GLOW_PURPLE)

        start_x2 = x + (w - (box_w * len(row2) + 20 * (len(row2) - 1))) // 2
        for j, label in enumerate(row2):
            idx = len(row1) + j + 1
            bx = start_x2 + j * (box_w + 20)
            _draw_card(draw, bx, y2, box_w, box_h, radius=10, fill=CARD_BG, outline=GLOW_CYAN)
            draw.text((bx + 8, y2 + 6), f'0{idx}', font=fonts['small'], fill=GLOW_PURPLE)
            draw.text((bx + 10, y2 + 28), textwrap.shorten(label, width=20, placeholder='…'), font=fonts['small_bold'], fill=TEXT_WHITE)
            if j < len(row2) - 1:
                ax = bx + box_w + 3
                draw.line([(ax, y2 + box_h // 2), (ax + 14, y2 + box_h // 2)], fill=GLOW_PURPLE, width=3)
                draw.polygon([(ax + 14, y2 + box_h // 2), (ax + 8, y2 + box_h // 2 - 4), (ax + 8, y2 + box_h // 2 + 4)], fill=GLOW_PURPLE)


def _draw_tree(draw, data, area, fonts):
    x, y, w, h = area
    nodes = data.get('nodes', [])
    root_label = 'Core Concept'
    children = []

    if nodes and isinstance(nodes[0], dict):
        root_label = nodes[0].get('label', 'Root')
        children = nodes[0].get('children', [])
    elif nodes:
        root_label = str(nodes[0])
        children = nodes[1:]
    else:
        children = data.get('children', ['Component A', 'Component B', 'Component C'])

    root_w = 200
    root_h = 56
    root_x = x + (w - root_w) // 2
    root_y = y + 20
    _draw_card(draw, root_x, root_y, root_w, root_h, radius=12, fill=(45, 38, 90), outline=GLOW_PURPLE)
    draw.text((root_x + 15, root_y + 16), textwrap.shorten(str(root_label), width=22, placeholder='…'), font=fonts['sub'], fill=TEXT_WHITE)

    if not children:
        return

    children = children[:5]
    child_w = min(140, max(90, (w - 20 * (len(children) - 1)) // len(children)))
    child_h = 52
    total_child_w = child_w * len(children) + 20 * (len(children) - 1)
    child_start_x = x + (w - total_child_w) // 2
    child_y = y + h - child_h - 20

    stem_mid_y = root_y + root_h + 30
    draw.line([(x + w // 2, root_y + root_h), (x + w // 2, stem_mid_y)], fill=GLOW_PURPLE, width=3)

    for i, child in enumerate(children):
        cx = child_start_x + i * (child_w + 20)
        c_mid = cx + child_w // 2

        draw.line([(x + w // 2, stem_mid_y), (c_mid, stem_mid_y)], fill=GLOW_PURPLE, width=2)
        draw.line([(c_mid, stem_mid_y), (c_mid, child_y)], fill=GLOW_CYAN, width=2)

        _draw_card(draw, cx, child_y, child_w, child_h, radius=10, fill=CARD_BG, outline=GLOW_CYAN)
        c_text = child.get('label', str(child)) if isinstance(child, dict) else str(child)
        draw.text((cx + 8, child_y + 16), textwrap.shorten(c_text, width=16, placeholder='…'), font=fonts['small_bold'], fill=TEXT_WHITE)


def _draw_chart(draw, data, area, fonts, line=False):
    x, y, w, h = area
    labels = [str(item) for item in data.get('labels', [])[:7]]
    raw_vals = data.get('values', [])
    values = []
    for v in raw_vals[: len(labels)]:
        try:
            values.append(float(v))
        except (ValueError, TypeError):
            values.append(0.0)

    if not values or not labels:
        labels = ['Step 1', 'Step 2', 'Step 3', 'Step 4']
        values = [30.0, 65.0, 45.0, 90.0]

    left = x + 50
    right = x + w - 30
    top = y + 45
    bottom = y + h - 45

    max_v = max(max(values), 1.0) * 1.15

    for step in range(4):
        gy = bottom - (step / 3.0) * (bottom - top)
        draw.line([(left, gy), (right, gy)], fill=(45, 50, 80), width=1)
        val_label = f'{int((step / 3.0) * max_v)}'
        draw.text((left - 38, gy - 8), val_label, font=fonts['small'], fill=TEXT_MUTED)

    draw.line([(left, top - 10), (left, bottom)], fill=PANEL_BORDER, width=2)
    draw.line([(left, bottom), (right, bottom)], fill=PANEL_BORDER, width=2)

    num_points = len(values)
    points = []
    step_w = (right - left) / max(num_points, 1)

    for i, v in enumerate(values):
        px = left + step_w * (i + 0.5)
        py = bottom - (v / max_v) * (bottom - top)
        points.append((px, py))

    if line:
        if len(points) > 1:
            draw.line(points, fill=GLOW_CYAN, width=4)
        for px, py in points:
            draw.ellipse((px - 7, py - 7, px + 7, py + 7), fill=GLOW_PURPLE, outline=TEXT_WHITE, width=2)
            draw.text((px - 12, py - 22), f'{int(values[points.index((px, py))])}', font=fonts['small_bold'], fill=TEXT_WHITE)
    else:
        bar_w = min(55, max(26, int(step_w * 0.55)))
        for i, (px, py) in enumerate(points):
            draw.rounded_rectangle((px - bar_w // 2, py, px + bar_w // 2, bottom), radius=6, fill=GLOW_PURPLE, outline=GLOW_CYAN, width=1)
            draw.text((px - 14, py - 22), f'{int(values[i])}', font=fonts['small_bold'], fill=GLOW_CYAN)

    for i, label in enumerate(labels):
        px = points[i][0]
        short_lbl = textwrap.shorten(label, width=10, placeholder='..')
        draw.text((px - 22, bottom + 12), short_lbl, font=fonts['small'], fill=TEXT_MUTED)


def _draw_table(draw, data, area, fonts):
    x, y, w, h = area
    columns = data.get('columns', ['Property', 'Description', 'Example'])[:4]
    rows = data.get('rows', [])[:5]

    if not rows:
        rows = [
            ['Definition', 'Core rule', 'Standard'],
            ['Complexity', 'Time & space cost', 'O(log n)'],
            ['Requirement', 'Input constraints', 'Sorted list'],
        ]

    col_w = w // max(len(columns), 1)
    header_h = 38
    row_h = min(46, (h - header_h) // max(len(rows), 1))

    draw.rounded_rectangle((x, y, x + w, y + header_h), radius=8, fill=(45, 38, 90), outline=GLOW_PURPLE)
    for ci, col in enumerate(columns):
        draw.text((x + ci * col_w + 14, y + 10), str(col)[:18], font=fonts['small_bold'], fill=TEXT_WHITE)

    for ri, row in enumerate(rows):
        ry = y + header_h + ri * row_h
        bg = (24, 28, 56) if ri % 2 == 0 else (30, 35, 68)
        draw.rectangle((x, ry, x + w, ry + row_h), fill=bg, outline=(45, 52, 90))
        for ci, cell in enumerate(row[: len(columns)]):
            draw.text((x + ci * col_w + 14, ry + 12), str(cell)[:22], font=fonts['small'], fill=TEXT_MUTED)


def _draw_chain(draw, data, area, fonts, kind='linked-list'):
    x, y, w, h = area
    nodes = data.get('nodes', ['HEAD', 'Node 1', 'Node 2', 'Node 3', 'NULL'])[:6]
    gap = 22
    box_w = min(130, (w - gap * (len(nodes) - 1)) // max(len(nodes), 1))
    box_h = 66
    start_x = x + (w - (box_w * len(nodes) + gap * (len(nodes) - 1))) // 2
    cy = y + (h - box_h) // 2

    for i, node in enumerate(nodes):
        bx = start_x + i * (box_w + gap)
        label = node.get('label', str(node)) if isinstance(node, dict) else str(node)
        border_col = GLOW_CYAN if i in (0, len(nodes) - 1) else GLOW_PURPLE
        _draw_card(draw, bx, cy, box_w, box_h, radius=10, fill=CARD_BG, outline=border_col)

        sub = 'POINTER' if i == 0 else 'NIL' if i == len(nodes) - 1 else f'DATA {i}'
        draw.text((bx + 10, cy + 8), sub, font=fonts['small'], fill=GLOW_CYAN)
        draw.text((bx + 12, cy + 32), textwrap.shorten(label, width=14, placeholder='…'), font=fonts['small_bold'], fill=TEXT_WHITE)

        if i < len(nodes) - 1:
            ax = bx + box_w + 2
            mid_y = cy + box_h // 2
            draw.line([(ax, mid_y), (ax + gap - 4, mid_y)], fill=GLOW_CYAN, width=3)
            draw.polygon([(ax + gap - 4, mid_y), (ax + gap - 10, mid_y - 4), (ax + gap - 10, mid_y + 4)], fill=GLOW_CYAN)


def _render_definition_slide(draw, scene, fonts):
    term = scene.get('title') or 'Key Term Definition'
    definition = scene.get('definition') or scene.get('narration') or ''
    intuition = scene.get('intuition') or scene.get('simpleExplanation') or 'Think of this as the building block of the concept.'
    why_matters = scene.get('whyItMatters') or 'Understanding this term prevents confusion in subsequent steps.'

    _draw_card(draw, 70, 160, 480, 470, radius=20, fill=(24, 28, 56), outline=PANEL_BORDER)
    draw.rounded_rectangle((95, 185, 245, 215), radius=8, fill=(45, 38, 90))
    draw.text((105, 192), 'TERM GLOSSARY', font=fonts['small_bold'], fill=GLOW_CYAN)

    draw.text((95, 235), textwrap.shorten(term, width=30, placeholder='…'), font=fonts['display'], fill=TEXT_WHITE)
    draw.text((95, 290), 'WHY THIS MATTERS', font=fonts['small_bold'], fill=TEXT_HIGHLIGHT)
    why_wrapped = _wrap_text(why_matters, width=38)
    draw.text((95, 320), why_wrapped, font=fonts['body'], fill=TEXT_MUTED, spacing=6)

    key_points = scene.get('keyPoints', [])
    if key_points:
        why_lines = len(why_wrapped.split("\n"))
        props_y = min(470, max(425, 320 + why_lines * 25 + 15))
        draw.text((95, props_y), 'ESSENTIAL PROPERTIES', font=fonts['small_bold'], fill=TEXT_HIGHLIGHT)
        max_pts = 2 if props_y > 440 else 3
        for idx, pt in enumerate(key_points[:max_pts]):
            pt_y = props_y + 28 + idx * 32
            draw.ellipse((95, pt_y + 5, 103, pt_y + 13), fill=GLOW_PURPLE)
            draw.text((115, pt_y), textwrap.shorten(str(pt), width=42, placeholder='…'), font=fonts['small'], fill=TEXT_WHITE)

    _draw_card(draw, 580, 160, 630, 470, radius=20, fill=(24, 28, 56), outline=GLOW_PURPLE)

    _draw_card(draw, 610, 190, 570, 200, radius=16, fill=CARD_BG, outline=GLOW_PURPLE)
    draw.text((635, 210), 'FORMAL DEFINITION', font=fonts['small_bold'], fill=GLOW_CYAN)
    draw.text((635, 245), _wrap_text(definition, width=46), font=fonts['body_bold'], fill=TEXT_WHITE, spacing=8)

    _draw_card(draw, 610, 410, 570, 190, radius=16, fill=(35, 45, 75), outline=GLOW_CYAN)
    draw.text((635, 430), 'IN SIMPLE WORDS (PLAIN INTUITION)', font=fonts['small_bold'], fill=GLOW_EMERALD)
    draw.text((635, 465), _wrap_text(intuition, width=46), font=fonts['body'], fill=TEXT_MUTED, spacing=6)


def _render_quiz_slide(draw, scene, fonts):
    quiz = scene.get('quiz') or {}
    question = quiz.get('question') or scene.get('narration') or 'Quick Knowledge Check:'
    options = quiz.get('options', ['Option A', 'Option B', 'Option C', 'Option D'])
    answer_idx = int(quiz.get('answerIndex', 0))
    explanation = quiz.get('explanation') or 'Review the core principle explained in the previous slide.'

    _draw_card(draw, 70, 160, 1140, 120, radius=18, fill=(32, 28, 68), outline=GLOW_PURPLE)
    draw.rounded_rectangle((95, 175, 285, 203), radius=6, fill=GLOW_PURPLE)
    draw.text((105, 180), 'KNOWLEDGE CHECKPOINT', font=fonts['small_bold'], fill=TEXT_WHITE)
    draw.text((95, 215), textwrap.shorten(question, width=82, placeholder='…'), font=fonts['title'], fill=TEXT_WHITE)

    grid_w = 555
    grid_h = 82
    coords = [
        (70, 300),
        (655, 300),
        (70, 395),
        (655, 395),
    ]

    for idx, opt in enumerate(options[:4]):
        gx, gy = coords[idx]
        is_correct = (idx == answer_idx)
        border_col = GLOW_EMERALD if is_correct else CARD_BORDER
        fill_col = (25, 45, 45) if is_correct else CARD_BG

        _draw_card(draw, gx, gy, grid_w, grid_h, radius=14, fill=fill_col, outline=border_col)

        badge_fill = GLOW_EMERALD if is_correct else (50, 45, 80)
        draw.rounded_rectangle((gx + 16, gy + 16, gx + 52, gy + 66), radius=8, fill=badge_fill)
        draw.text((gx + 26, gy + 28), chr(65 + idx), font=fonts['sub'], fill=TEXT_WHITE)

        draw.text((gx + 66, gy + 28), textwrap.shorten(str(opt), width=44, placeholder='…'), font=fonts['body_bold'], fill=TEXT_WHITE)

        if is_correct:
            draw.text((gx + grid_w - 115, gy + 30), '[CORRECT]', font=fonts['small_bold'], fill=GLOW_EMERALD)

    _draw_card(draw, 70, 495, 1140, 135, radius=16, fill=(20, 32, 50), outline=GLOW_CYAN)
    draw.text((95, 510), 'EXPLANATION & TAKEAWAY', font=fonts['small_bold'], fill=GLOW_CYAN)
    draw.text((95, 538), _wrap_text(explanation, width=105), font=fonts['body'], fill=TEXT_MUTED, spacing=6)


def generate_visual(title: str, scene: dict, output_path: str):
    if not isinstance(scene, dict):
        scene = {'narration': str(scene), 'keyPoints': [], 'visual': {'type': 'none', 'data': {}}}

    image = Image.new('RGB', (1280, 720), color=BG_DARK)
    _draw_gradient_bg(image)
    draw = ImageDraw.Draw(image)
    fonts = _fonts()

    draw.rounded_rectangle((35, 30, 1245, 690), radius=24, fill=(18, 22, 44), outline=(48, 54, 90), width=2)

    scene_title = str(scene.get('title') or title or 'Learnify AI Lecture')
    draw.text((70, 56), textwrap.shorten(scene_title, width=62, placeholder='…'), fill=TEXT_WHITE, font=fonts['display'])

    kind = (scene.get('visual') or {}).get('type', 'concept')
    stage_text = f'LEARNIFY AI  •  3D MASTERCLASS  •  {kind.upper()}'
    draw.rounded_rectangle((70, 108, 380, 134), radius=6, fill=(35, 30, 75))
    draw.text((80, 113), stage_text, fill=GLOW_CYAN, font=fonts['small_bold'])

    slide_type = scene.get('slideType') or kind

    if slide_type == 'definition':
        _render_definition_slide(draw, scene, fonts)
    elif slide_type == 'quiz' or 'quiz' in scene:
        _render_quiz_slide(draw, scene, fonts)
    else:
        _draw_card(draw, 70, 160, 510, 470, radius=20, fill=(24, 28, 56), outline=PANEL_BORDER)

        draw.text((95, 185), 'TEACHER EXPLANATION', font=fonts['small_bold'], fill=GLOW_CYAN)
        narration = scene.get('narration', '')
        draw.text((95, 218), _wrap_text(narration[:550], width=38), font=fonts['body'], fill=TEXT_MUTED, spacing=7)

        key_points = scene.get('keyPoints') or []
        if key_points:
            draw.text((95, 455), 'CORE TAKEAWAYS', font=fonts['small_bold'], fill=TEXT_HIGHLIGHT)
            for idx, pt in enumerate(key_points[:3]):
                draw.ellipse((95, 488 + idx * 36, 103, 496 + idx * 36), fill=GLOW_PURPLE)
                draw.text((115, 482 + idx * 36), textwrap.shorten(str(pt), width=42, placeholder='…'), font=fonts['small'], fill=TEXT_WHITE)

        _draw_card(draw, 605, 160, 605, 470, radius=20, fill=(24, 28, 56), outline=GLOW_PURPLE)
        visual = scene.get('visual') or {}
        v_type = visual.get('type', 'flowchart')
        v_data = visual.get('data') or {}

        v_title = visual.get('title') or 'Visual Representation'
        draw.text((630, 185), textwrap.shorten(v_title, width=42, placeholder='…'), font=fonts['sub'], fill=TEXT_WHITE)

        v_area = (625, 230, 565, 370)

        if v_type in {'linked-list', 'stack', 'queue', 'array', 'memory', 'binary'}:
            _draw_chain(draw, v_data, v_area, fonts, kind=v_type)
        elif v_type in {'bar-chart', 'scatter-plot'}:
            _draw_chart(draw, v_data, v_area, fonts, line=False)
        elif v_type == 'line-chart':
            _draw_chart(draw, v_data, v_area, fonts, line=True)
        elif v_type in {'tree', 'graph'}:
            _draw_tree(draw, v_data, v_area, fonts)
        elif v_type in {'comparison-table', 'table'}:
            _draw_table(draw, v_data, v_area, fonts)
        else:
            _draw_flow(draw, v_data, v_area, fonts)

    draw.line([(70, 646), (1210, 646)], fill=(45, 50, 85), width=1)
    draw.text((70, 656), 'Learnify AI  •  Deep Conceptual Mastery  •  Interactive Lecture', font=fonts['small'], fill=TEXT_MUTED)

    image.save(output_path, quality=95)
