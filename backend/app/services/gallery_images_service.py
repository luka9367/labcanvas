"""Generate high-quality academic-style placeholder images for gallery items."""
import json
import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random

logger = logging.getLogger(__name__)

GALLERY_DIR = Path(__file__).parent.parent / "static" / "gallery"
GALLERY_DATA_PATH = GALLERY_DIR / "gallery.json"

# Morandi color palette (soft, muted tones)
MORANDI_COLORS = {
    "primary": [(129, 152, 165), (97, 122, 137), (76, 100, 115)],      # Dusty blue
    "secondary": [(168, 157, 147), (142, 131, 122), (116, 106, 98)],   # Warm gray
    "accent1": [(186, 168, 156), (163, 145, 133), (140, 123, 112)],    # Beige
    "accent2": [(152, 168, 148), (128, 144, 124), (105, 120, 101)],    # Sage green
    "accent3": [(176, 159, 172), (153, 137, 149), (131, 116, 127)],    # Muted purple
    "accent4": [(191, 168, 148), (168, 146, 127), (145, 124, 106)],    # Tan
    "background": [(250, 248, 245), (245, 243, 240), (240, 238, 235)],  # Warm white
    "text": [(80, 80, 82), (100, 100, 102), (120, 120, 122)],          # Dark gray
    "grid": [(220, 218, 215), (210, 208, 205)],                        # Light grid
}

# Category to color mapping
CATEGORY_COLORS = {
    "pipeline": "primary",
    "architecture": "accent2",
    "framework": "accent3",
    "table": "accent1",
    "concept_map": "accent4",
    "comparison": "secondary",
    "freeform": "primary",
}


def get_font(size: int, bold: bool = False):
    """Get a font for drawing text."""
    font_paths = [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/simhei.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    
    for font_path in font_paths:
        try:
            return ImageFont.truetype(font_path, size)
        except:
            continue
    
    return ImageFont.load_default()


def draw_dotted_background(draw: ImageDraw.Draw, size: tuple, color: tuple):
    """Draw subtle dot grid background."""
    dot_spacing = 20
    dot_radius = 1
    for x in range(0, size[0], dot_spacing):
        for y in range(0, size[1], dot_spacing):
            draw.ellipse(
                [x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius],
                fill=color
            )


def draw_rounded_rect(draw: ImageDraw.Draw, bbox: tuple, radius: int, fill: tuple, outline: tuple = None, width: int = 1):
    """Draw a rounded rectangle."""
    x1, y1, x2, y2 = bbox
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=outline, width=width)


def draw_dashed_border(draw: ImageDraw.Draw, bbox: tuple, radius: int, color: tuple, width: int = 2, dash_length: int = 8):
    """Draw a dashed border around a rounded rectangle."""
    x1, y1, x2, y2 = bbox
    
    # Top edge
    for x in range(x1 + radius, x2 - radius, dash_length * 2):
        draw.line([(x, y1), (min(x + dash_length, x2 - radius), y1)], fill=color, width=width)
    
    # Bottom edge
    for x in range(x1 + radius, x2 - radius, dash_length * 2):
        draw.line([(x, y2), (min(x + dash_length, x2 - radius), y2)], fill=color, width=width)
    
    # Left edge
    for y in range(y1 + radius, y2 - radius, dash_length * 2):
        draw.line([(x1, y), (x1, min(y + dash_length, y2 - radius))], fill=color, width=width)
    
    # Right edge
    for y in range(y1 + radius, y2 - radius, dash_length * 2):
        draw.line([(x2, y), (x2, min(y + dash_length, y2 - radius))], fill=color, width=width)
    
    # Corners (simplified as small arcs)
    corner_radius = radius
    # Top-left corner
    draw.arc([x1, y1, x1 + corner_radius * 2, y1 + corner_radius * 2], 180, 270, fill=color, width=width)
    # Top-right corner
    draw.arc([x2 - corner_radius * 2, y1, x2, y1 + corner_radius * 2], 270, 360, fill=color, width=width)
    # Bottom-left corner
    draw.arc([x1, y2 - corner_radius * 2, x1 + corner_radius * 2, y2], 90, 180, fill=color, width=width)
    # Bottom-right corner
    draw.arc([x2 - corner_radius * 2, y2 - corner_radius * 2, x2, y2], 0, 90, fill=color, width=width)


def draw_arrow(draw: ImageDraw.Draw, start: tuple, end: tuple, fill: tuple, width: int = 2):
    """Draw an arrow with rounded style."""
    draw.line([start, end], fill=fill, width=width)
    
    # Draw arrowhead
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = (dx ** 2 + dy ** 2) ** 0.5
    
    if length > 0:
        # Normalize
        dx /= length
        dy /= length
        
        # Arrowhead size
        arrow_size = 8
        
        # Calculate arrowhead points
        p1 = (end[0] - arrow_size * dx + arrow_size * 0.5 * dy, end[1] - arrow_size * dy - arrow_size * 0.5 * dx)
        p2 = (end[0] - arrow_size * dx - arrow_size * 0.5 * dy, end[1] - arrow_size * dy + arrow_size * 0.5 * dx)
        
        draw.polygon([p1, end, p2], fill=fill)


def draw_icon(draw: ImageDraw.Draw, icon_type: str, bbox: tuple, color: tuple):
    """Draw a simple flat icon."""
    x1, y1, x2, y2 = bbox
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    size = min(x2 - x1, y2 - y1)
    
    if icon_type == "robot":
        # Robot head
        head_size = size // 2
        draw.rounded_rectangle(
            [cx - head_size//2, cy - head_size//2, cx + head_size//2, cy + head_size//2],
            radius=4, fill=color
        )
        # Eyes
        eye_size = head_size // 6
        draw.ellipse([cx - head_size//4 - eye_size, cy - eye_size, cx - head_size//4 + eye_size, cy + eye_size], fill=(255, 255, 255))
        draw.ellipse([cx + head_size//4 - eye_size, cy - eye_size, cx + head_size//4 + eye_size, cy + eye_size], fill=(255, 255, 255))
    
    elif icon_type == "lightbulb":
        # Lightbulb
        bulb_size = size // 3
        draw.ellipse([cx - bulb_size, cy - bulb_size, cx + bulb_size, cy + bulb_size], fill=color)
        # Base
        draw.rectangle([cx - bulb_size//2, cy + bulb_size, cx + bulb_size//2, cy + bulb_size + bulb_size//2], fill=color)
    
    elif icon_type == "document":
        # Document
        doc_w = size // 2
        doc_h = size * 2 // 3
        draw.rounded_rectangle([cx - doc_w//2, cy - doc_h//2, cx + doc_w//2, cy + doc_h//2], radius=3, fill=color)
        # Lines
        for i in range(3):
            y = cy - doc_h//4 + i * doc_h//6
            draw.line([(cx - doc_w//3, y), (cx + doc_w//3, y)], fill=(255, 255, 255), width=2)
    
    elif icon_type == "question":
        # Question mark circle
        r = size // 3
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=3)
        q_font = get_font(r)
        draw.text((cx - r//4, cy - r//2), "?", fill=color, font=q_font)


def generate_academic_placeholder(item: dict, size: tuple = (800, 600)) -> Image.Image:
    """Generate a high-quality academic-style placeholder image matched to category."""
    category = item.get("category", "pipeline")
    color_key = CATEGORY_COLORS.get(category, "primary")
    colors = MORANDI_COLORS[color_key]
    bg_colors = MORANDI_COLORS["background"]
    text_colors = MORANDI_COLORS["text"]
    grid_color = MORANDI_COLORS["grid"][0]
    
    img = Image.new('RGB', size, bg_colors[0])
    draw = ImageDraw.Draw(img)
    
    # Draw dotted grid background
    draw_dotted_background(draw, size, grid_color)
    
    # Subtle top-to-bottom gradient
    for y in range(size[1]):
        alpha = int(6 * (1 - y / size[1]))
        r = min(255, bg_colors[0][0] + alpha)
        g = min(255, bg_colors[0][1] + alpha)
        b = min(255, bg_colors[0][2] + alpha)
        draw.line([(0, y), (size[0], y)], fill=(r, g, b))
    
    margin = 45
    content_bbox = (margin, margin + 25, size[0] - margin, size[1] - margin - 25)
    
    # White card background
    draw_rounded_rect(draw, content_bbox, radius=16, fill=(255, 255, 255), outline=None, width=0)
    # Soft dashed border
    draw_dashed_border(draw, content_bbox, radius=16, color=colors[1], width=2, dash_length=10)
    
    # Category badge
    badge_font = get_font(11, bold=True)
    badge_text = category.upper()
    bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
    badge_w = bbox[2] - bbox[0] + 16
    badge_h = bbox[3] - bbox[1] + 8
    bx = margin + 18
    by = margin + 38
    draw_rounded_rect(draw, (bx, by, bx + badge_w, by + badge_h), radius=4, fill=colors[0], outline=colors[1], width=1)
    draw.text((bx + 8, by + 4), badge_text, fill=(255, 255, 255), font=badge_font)
    
    # Title wrapping
    title = item.get("name", item.get("title", "Unknown"))
    title_font = get_font(17, bold=True)
    max_w = size[0] - margin * 2 - 45
    words = title.split()
    lines = []
    cur = []
    for w in words:
        test = ' '.join(cur + [w])
        tb = draw.textbbox((0, 0), test, font=title_font)
        if tb[2] - tb[0] <= max_w:
            cur.append(w)
        else:
            if cur:
                lines.append(' '.join(cur))
            cur = [w]
    if cur:
        lines.append(' '.join(cur))
    lines = lines[:3]
    
    y_off = by + badge_h + 18
    for i, line in enumerate(lines):
        draw.text((margin + 22, y_off + i * 26), line, fill=text_colors[0], font=title_font)
    
    diagram_y = y_off + len(lines) * 26 + 20
    
    # ── Category-specific diagram layouts ──────────────────────────────
    if category == "pipeline":
        _draw_pipeline(draw, diagram_y, margin, size, colors, bg_colors, text_colors)
    elif category == "architecture":
        _draw_architecture(draw, diagram_y, margin, size, colors, text_colors)
    elif category == "framework":
        _draw_framework(draw, diagram_y, margin, size, colors, bg_colors, text_colors)
    elif category == "table":
        _draw_table(draw, diagram_y, margin, size, colors, bg_colors, text_colors)
    elif category == "concept_map":
        _draw_concept_map(draw, diagram_y, margin, size, colors, bg_colors, text_colors)
    elif category == "comparison":
        _draw_comparison(draw, diagram_y, margin, size, colors, bg_colors, text_colors)
    else:
        _draw_generic(draw, diagram_y, margin, size, colors, bg_colors, text_colors, grid_color)
    
    # Year / conference badge bottom-right
    year = item.get("year", "")
    conf = item.get("conference", "")
    if year or conf:
        info_font = get_font(10)
        info_text = f"{year} · {conf}" if year and conf else (year or conf)
        bbox = draw.textbbox((0, 0), info_text, font=info_font)
        iw = bbox[2] - bbox[0] + 14
        ih = bbox[3] - bbox[1] + 6
        ix = size[0] - margin - iw - 12
        iy = size[1] - margin - 38
        draw_rounded_rect(draw, (ix, iy, ix + iw, iy + ih), radius=3, fill=colors[0], outline=None)
        draw.text((ix + 7, iy + 3), info_text, fill=(255, 255, 255), font=info_font)
    
    return img


def _draw_pipeline(draw, y, margin, size, colors, bg_colors, text_colors):
    box_w = (size[0] - margin * 2 - 70) // 3
    box_h = 85
    icons = ["question", "robot", "lightbulb"]
    for i in range(3):
        bx = margin + 30 + i * (box_w + 22)
        draw_rounded_rect(draw, (bx, y, bx + box_w, y + box_h), radius=10, fill=bg_colors[1], outline=colors[0], width=2)
        draw_icon(draw, icons[i], (bx + box_w // 2 - 18, y + 8, bx + box_w // 2 + 18, y + 44), colors[1])
        lbl = get_font(12, bold=True)
        t = f"Step {i+1}"
        tb = draw.textbbox((0, 0), t, font=lbl)
        draw.text((bx + (box_w - (tb[2] - tb[0])) // 2, y + 54), t, fill=text_colors[1], font=lbl)
        if i < 2:
            draw_arrow(draw, (bx + box_w + 4, y + box_h // 2), (bx + box_w + 18, y + box_h // 2), colors[1], 2)


def _draw_architecture(draw, y, margin, size, colors, text_colors):
    layer_h = 50
    layer_w = size[0] - margin * 2 - 60
    layers = ["Input Layer", "Hidden Representation", "Output Layer"]
    layer_cols = [colors[0], colors[1], colors[2]]
    for i, (lbl, c) in enumerate(zip(layers, layer_cols)):
        lx = margin + 30
        ly = y + i * (layer_h + 12)
        draw_rounded_rect(draw, (lx, ly, lx + layer_w, ly + layer_h), radius=8, fill=c, outline=colors[2], width=1)
        lf = get_font(12, bold=True)
        tb = draw.textbbox((0, 0), lbl, font=lf)
        draw.text((lx + (layer_w - (tb[2] - tb[0])) // 2, ly + 16), lbl, fill=(255, 255, 255), font=lf)
        if i < 2:
            cy = ly + layer_h + 6
            draw.line([(lx + layer_w // 2 - 8, cy), (lx + layer_w // 2 + 8, cy)], fill=colors[1], width=2)
            draw.polygon([(lx + layer_w // 2, cy + 5), (lx + layer_w // 2 - 4, cy), (lx + layer_w // 2 + 4, cy)], fill=colors[1])


def _draw_framework(draw, y, margin, size, colors, bg_colors, text_colors):
    # Central hub with 4 surrounding modules
    cx = size[0] // 2
    cy = y + 70
    # Central circle
    r = 35
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=colors[0], outline=colors[2], width=2)
    hf = get_font(11, bold=True)
    draw.text((cx - 22, cy - 6), "Core", fill=(255, 255, 255), font=hf)
    # Modules
    mods = ["Data", "Model", "Train", "Eval"]
    pos = [(-90, 0), (90, 0), (0, -55), (0, 55)]
    for (dx, dy), m in zip(pos, mods):
        mx = cx + dx - 32
        my = cy + dy - 14
        draw_rounded_rect(draw, (mx, my, mx + 64, my + 28), radius=6, fill=bg_colors[1], outline=colors[0], width=2)
        mf = get_font(10, bold=True)
        tb = draw.textbbox((0, 0), m, font=mf)
        draw.text((mx + (64 - (tb[2] - tb[0])) // 2, my + 6), m, fill=text_colors[1], font=mf)
        # Connect to center
        if dx != 0:
            sx = mx + (64 if dx < 0 else 0)
            ex = cx + (-r if dx < 0 else r)
            draw.line([(sx, my + 14), (ex, cy + dy // 3)], fill=colors[1], width=2)
        else:
            sy = my + (28 if dy < 0 else 0)
            ey = cy + (-r if dy < 0 else r)
            draw.line([(mx + 32, sy), (cx + dx // 3, ey)], fill=colors[1], width=2)


def _draw_table(draw, y, margin, size, colors, bg_colors, text_colors):
    # Draw a benchmark / comparison table
    cols = 4
    rows = 4
    col_w = (size[0] - margin * 2 - 60) // cols
    row_h = 32
    tx = margin + 30
    ty = y + 10
    # Header
    draw_rounded_rect(draw, (tx, ty, tx + col_w * cols, ty + row_h), radius=4, fill=colors[0], outline=colors[2], width=1)
    hf = get_font(10, bold=True)
    headers = ["Method", "Acc ↑", "F1 ↑", "Params"]
    for i, h in enumerate(headers):
        draw.text((tx + i * col_w + 8, ty + 8), h, fill=(255, 255, 255), font=hf)
    # Rows
    rf = get_font(10)
    for r in range(1, rows):
        ry = ty + r * row_h
        bg = bg_colors[1] if r % 2 == 0 else (255, 255, 255)
        draw.rectangle([tx, ry, tx + col_w * cols, ry + row_h], fill=bg, outline=colors[1], width=1)
        vals = [f"Model-{r}", f"{0.85 + r * 0.03:.2f}", f"{0.82 + r * 0.02:.2f}", f"{12 + r * 3}M"]
        for i, v in enumerate(vals):
            draw.text((tx + i * col_w + 8, ry + 8), v, fill=text_colors[1], font=rf)


def _draw_concept_map(draw, y, margin, size, colors, bg_colors, text_colors):
    # Nodes connected as a graph
    nodes = [(0.2, 0.15), (0.5, 0.05), (0.8, 0.15), (0.35, 0.45), (0.65, 0.45), (0.5, 0.75)]
    labels = ["Input", "Embed", "Token", "Fusion", "Graph", "Output"]
    nx = size[0] - margin * 2 - 60
    ny = 140
    cx = margin + 30
    cy = y + 10
    node_positions = []
    for (px, py), lbl in zip(nodes, labels):
        x = cx + int(px * nx)
        yp = cy + int(py * ny)
        r = 22
        draw.ellipse([x - r, yp - r, x + r, yp + r], fill=colors[0] if px == 0.5 and py == 0.75 else bg_colors[1], outline=colors[1], width=2)
        nf = get_font(9, bold=True)
        tb = draw.textbbox((0, 0), lbl, font=nf)
        draw.text((x - (tb[2] - tb[0]) // 2, yp - 6), lbl, fill=(255, 255, 255) if (px == 0.5 and py == 0.75) else text_colors[1], font=nf)
        node_positions.append((x, yp))
    # Edges
    edges = [(0, 1), (1, 2), (0, 3), (2, 4), (3, 5), (4, 5), (1, 4)]
    for a, b in edges:
        x1, y1 = node_positions[a]
        x2, y2 = node_positions[b]
        draw.line([(x1, y1), (x2, y2)], fill=colors[1], width=2)


def _draw_comparison(draw, y, margin, size, colors, bg_colors, text_colors):
    # Two-column comparison bars
    bar_h = 22
    gap = 10
    left_x = margin + 35
    right_x = size[0] // 2 + 20
    pairs = [("Ours", 0.92), ("Baseline", 0.78), ("Ours", 0.88), ("Baseline", 0.72)]
    for i in range(2):
        by = y + 10 + i * (bar_h * 2 + gap + 18)
        label = ["Accuracy", "F1-Score"][i]
        lf = get_font(10, bold=True)
        draw.text((left_x, by - 16), label, fill=text_colors[0], font=lf)
        # Bars
        for j, (name, val) in enumerate([(pairs[i * 2]), (pairs[i * 2 + 1])]):
            bx = left_x if j == 0 else right_x
            bw = int(160 * val)
            bc = colors[0] if name == "Ours" else colors[1]
            draw_rounded_rect(draw, (bx, by, bx + bw, by + bar_h), radius=4, fill=bc, outline=None)
            vf = get_font(9, bold=True)
            draw.text((bx + 6, by + 4), f"{name} {val:.0%}", fill=(255, 255, 255), font=vf)


def _draw_generic(draw, y, margin, size, colors, bg_colors, text_colors, grid_color):
    block_w = (size[0] - margin * 2 - 50) // 2
    block_h = 78
    icons = [["document", "lightbulb"], ["robot", "question"]]
    for row in range(2):
        for col in range(2):
            bx = margin + 28 + col * (block_w + 18)
            by = y + row * (block_h + 16)
            draw_rounded_rect(draw, (bx, by, bx + block_w, by + block_h), radius=10, fill=bg_colors[1], outline=colors[0], width=1)
            draw_icon(draw, icons[row][col], (bx + 14, by + 14, bx + 50, by + 50), colors[1])
            ly = by + 18
            for j in range(3):
                lw = block_w - 70 - j * 8
                draw.line([(bx + 56, ly), (bx + 56 + lw, ly)], fill=grid_color, width=2)
                ly += 16


def init_gallery_images():
    """Initialize gallery images - generate placeholders if needed."""
    if not GALLERY_DATA_PATH.exists():
        logger.warning("Gallery data file not found: %s", GALLERY_DATA_PATH)
        return
    
    try:
        with open(GALLERY_DATA_PATH, 'r', encoding='utf-8') as f:
            gallery_data = json.load(f)
        
        GALLERY_DIR.mkdir(parents=True, exist_ok=True)
        
        generated_count = 0
        skipped_count = 0
        
        for item in gallery_data:
            image_id = item['id']
            image_path = GALLERY_DIR / f"{image_id}.jpg"
            
            if image_path.exists():
                skipped_count += 1
                continue
            
            try:
                img = generate_academic_placeholder(item)
                img.save(image_path, 'JPEG', quality=95)
                generated_count += 1
                
                if generated_count % 50 == 0:
                    logger.info(f"Generated {generated_count} academic-style placeholder images...")
                    
            except Exception as e:
                logger.error(f"Failed to generate image for {image_id}: {e}")
        
        logger.info(f"Gallery images initialized: {generated_count} generated, {skipped_count} skipped")
        
    except Exception as e:
        logger.error(f"Failed to initialize gallery images: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_gallery_images()
