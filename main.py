import pygame
import json
import os
import sys
import subprocess
import time

# --- Settings ---
SCREEN_W, SCREEN_H = 480, 270     # Native resolution
SCALE = 3                         # Window scale factor
BG_COLOR = (16, 16, 16)
TITLE = "Subpixel Depths"
VERSION = "Version 1.03a"
TITLE_SCALE = 1
VERSION_SCALE = 1
BTN_LABEL_SCALE = 1
BTN_WIDTH = 108      # 1x size from your mockup
BTN_HEIGHT = 35      # 1x size from your mockup
BTN_SPACING = 22     # 1x, adjust to taste
MARGIN_X = 30
MARGIN_Y = 48

# --- Asset Paths ---
def asset_path(filename):
    return os.path.join("Elements", filename)

FONT_FILE = asset_path("PixelOperator-Bold.png")
FONT_MAP = asset_path("PixelOperator-Bold.json")
FONT_REGULAR_FILE = asset_path("Pixolletta.png")
FONT_REGULAR_MAP = asset_path("Pixolletta.json")
BTN_IMAGE = asset_path("button_large_3state_9slice.png")
LOGO_IMAGE = asset_path("logo_newgamesquared.png")

# --- Bitmap Font Loading ---
def load_bitmap_font(img_path, json_path):
    img = pygame.image.load(img_path).convert_alpha()
    with open(json_path, "r") as f:
        cmap = {c['char']: (c['x'], c.get('y',0), c['width'], c.get('height',img.get_height()))
                for c in json.load(f)}
    return img, cmap

def draw_text(surface, text, x, y, font_img, font_cmap, color=(255,255,255), scale=1, space_px=3):
    orig_x = x
    for ch in text:
        if ch == '\n':
            y += font_img.get_height() * scale + 2
            x = orig_x
            continue
        if ch == ' ':
            # Use a custom width for spaces (default: 3 pixels per scale, looks best)
            x += space_px * scale
            continue
        if ch in font_cmap:
            sx, sy, sw, sh = font_cmap[ch]
            glyph = font_img.subsurface(pygame.Rect(sx, sy, sw, sh))
            glyph = pygame.transform.scale(glyph, (sw * scale, sh * scale))
            tint = glyph.copy()
            tint.fill(color + (0,), None, pygame.BLEND_RGB_MULT)
            surface.blit(tint, (x, y))
            x += (sw + 1) * scale
        else:
            x += 8 * scale  # fallback gap

# --- Button 9-slice ---
def draw_9slice_button(surface, x, y, w, h, state_img, scale=3):
    C, E = 12, 32  # CORNER & EDGE size at 1x

    # Corners (TopLeft, TopRight, BotLeft, BotRight)
    corners = [
        (0, 0, C, C),          # TL
        (44, 0, C, C),         # TR
        (0, 44, C, C),         # BL
        (44, 44, C, C)         # BR
    ]
    # Edges (src_x, src_y, src_w, src_h, dst_x, dst_y, dst_w, dst_h)
    edges = [
        (C, 0, E, C, x+C*scale, y, w-2*C*scale, C*scale),        # Top
        (C, 44, E, C, x+C*scale, y+h-C*scale, w-2*C*scale, C*scale),  # Bottom
        (0, C, C, E, x, y+C*scale, C*scale, h-2*C*scale),        # Left
        (44, C, C, E, x+w-C*scale, y+C*scale, C*scale, h-2*C*scale),  # Right
    ]
    center = (C, C, E, E)

    # Draw corners
    for idx, (sx, sy, sw, sh) in enumerate(corners):
        tile = state_img.subsurface(pygame.Rect(sx, sy, sw, sh))
        tile = pygame.transform.scale(tile, (sw*scale, sh*scale))
        dx = x if idx%2==0 else x+w-C*scale
        dy = y if idx<2 else y+h-C*scale
        surface.blit(tile, (dx, dy))
    # Draw edges
    for sx, sy, sw, sh, dx, dy, dw, dh in edges:
        tile = state_img.subsurface(pygame.Rect(sx, sy, sw, sh))
        tile = pygame.transform.scale(tile, (dw, dh))
        surface.blit(tile, (dx, dy))
    # Draw center
    sx, sy, sw, sh = center
    tile = state_img.subsurface(pygame.Rect(sx, sy, sw, sh))
    tile = pygame.transform.scale(tile, (w-2*C*scale, h-2*C*scale))
    surface.blit(tile, (x+C*scale, y+C*scale))

def draw_9slice(surface, x, y, w, h, img, csize=8):
    # Generic 9-slice for your popups (corners csize x csize)
    # img should be 3x3 grid: TL, T, TR, L, C, R, BL, B, BR
    sw, sh = img.get_width(), img.get_height()
    ts, cs = csize, csize
    # Slices
    # Corners
    TL = img.subsurface(pygame.Rect(0,0,cs,cs))
    TR = img.subsurface(pygame.Rect(sw-cs,0,cs,cs))
    BL = img.subsurface(pygame.Rect(0,sh-cs,cs,cs))
    BR = img.subsurface(pygame.Rect(sw-cs,sh-cs,cs,cs))
    # Edges
    T  = img.subsurface(pygame.Rect(cs,0,sw-2*cs,cs))
    B  = img.subsurface(pygame.Rect(cs,sh-cs,sw-2*cs,cs))
    L  = img.subsurface(pygame.Rect(0,cs,cs,sh-2*cs))
    R  = img.subsurface(pygame.Rect(sw-cs,cs,cs,sh-2*cs))
    # Center
    C  = img.subsurface(pygame.Rect(cs,cs,sw-2*cs,sh-2*cs))
    # Draw to surface
    surface.blit(TL, (x, y))
    surface.blit(TR, (x+w-cs, y))
    surface.blit(BL, (x, y+h-cs))
    surface.blit(BR, (x+w-cs, y+h-cs))
    # Edges
    surface.blit(pygame.transform.scale(T, (w-2*cs, cs)), (x+cs, y))
    surface.blit(pygame.transform.scale(B, (w-2*cs, cs)), (x+cs, y+h-cs))
    surface.blit(pygame.transform.scale(L, (cs, h-2*cs)), (x, y+cs))
    surface.blit(pygame.transform.scale(R, (cs, h-2*cs)), (x+w-cs, y+cs))
    # Center
    surface.blit(pygame.transform.scale(C, (w-2*cs, h-2*cs)), (x+cs, y+cs))

def draw_3slice_h(surface, x, y, w, img, lsize=8, rsize=8):
    # For headers and horizontal buttons
    sw, sh = img.get_width(), img.get_height()
    L = img.subsurface(pygame.Rect(0,0,lsize,sh))
    R = img.subsurface(pygame.Rect(sw-rsize,0,rsize,sh))
    M = img.subsurface(pygame.Rect(lsize,0,sw-lsize-rsize,sh))
    surface.blit(L, (x, y))
    surface.blit(R, (x+w-rsize, y))
    surface.blit(pygame.transform.scale(M, (w-lsize-rsize, sh)), (x+lsize, y))

def draw_3slice_button(surface, x, y, w, img, state=0):
    # img: 72x16 (3 states side by side), each state: 24x16 (L/M/R)
    L, M, R = 8, 8, 8
    x0 = state * 24  # ← Fix: states are side by side (horizontal)
    # Left cap
    surface.blit(img.subsurface((x0, 0, L, 16)), (x, y))
    # Middle stretch
    surface.blit(
        pygame.transform.scale(
            img.subsurface((x0 + L, 0, M, 16)),
            (w - L - R, 16)
        ), (x + L, y)
    )
    # Right cap
    surface.blit(img.subsurface((x0 + L + M, 0, R, 16)), (x + w - R, y))

def draw_3slice_v(surface, x, y, h, img, tsize=8, bsize=8):
    """
    Draws a vertical 3-slice using img:
    - tsize: height of top cap
    - bsize: height of bottom cap
    - img: should be vertically stacked: top, middle, bottom
    """
    sw, sh = img.get_width(), img.get_height()
    # Top cap
    surface.blit(img.subsurface((0, 0, sw, tsize)), (x, y))
    # Middle stretch
    surface.blit(
        pygame.transform.scale(
            img.subsurface((0, tsize, sw, sh-tsize-bsize)),
            (sw, h - tsize - bsize)
        ), (x, y + tsize)
    )
    # Bottom cap
    surface.blit(img.subsurface((0, sh-bsize, sw, bsize)), (x, y + h - bsize))

def get_text_width(text, font_img, font_cmap, scale=1):
    width = 0
    for ch in text:
        if ch in font_cmap:
            sx, sy, sw, sh = font_cmap[ch]
            width += sw * scale + 1
        else:
            width += 8 * scale
    return width

import glob

def pick_rom_file_modal(screen, font_img, font_cmap, font_regular_img, font_regular_cmap):
    # --- Load popup assets ---
    popup_img = pygame.image.load(asset_path("popup_main_9slice.png")).convert_alpha()
    header_img = pygame.image.load(asset_path("panel_headerspecial_3slice.png")).convert_alpha()
    close_btn_img = pygame.image.load(asset_path("button_closepopup_3state.png")).convert_alpha()
    std_btn_img = pygame.image.load(asset_path("button_standard_3state.png")).convert_alpha()
    scroll_bar_img = pygame.image.load(asset_path("button_scroll_bar.png")).convert_alpha()
    scroll_pos_img = pygame.image.load(asset_path("button_scroll_position.png")).convert_alpha()
    divider_img = pygame.image.load(asset_path("divider.png")).convert_alpha()

    # --- ROM list logic ---
    exts = ["*.smc", "*.sfc", "*.nes", "*.gen", "*.md", "*.gb", "*.gba"]
    rom_files = []
    for ext in exts:
        rom_files.extend(glob.glob(ext))
    rom_files = sorted(rom_files)

    if not rom_files:
        # Simple dialog for no files, reusing the modal graphics
        show_modal_message(screen, popup_img, header_img, font_img, font_cmap, "No ROM files found.\nPlace your ROMs next to main.py and try again.")
        return None

    # Popup geometry (native: 320x172, scaled up by current SCALE)
    scale = SCALE
    modal_w, modal_h = 320, 200  # <--- Increase height (try 200, tweak as needed)
    x = (screen.get_width() // scale - modal_w) // 2
    y = (screen.get_height() // scale - modal_h) // 2
    modal_rect = pygame.Rect(x*scale, y*scale, modal_w*scale, modal_h*scale)

    # Layout constants (all in native pixels)
    header_h = 21
    row_h = 14
    divider_gap = 10   # Gap between last row and divider
    btn_margin_bottom = 8
    list_x = 24
    list_y = header_h + 4    # was 36, now lines up better below the header
    btn_h = 16

    # Calculate how much vertical space for list items, *before* setting max_visible
    list_area = modal_h - list_y - btn_h - btn_margin_bottom - divider_gap
    max_visible = list_area // row_h

    scroll_h = (row_h * max_visible)
    list_x = 24
    list_y = header_h + 1    # was 36, now lines up better below the header
    list_w = modal_w - 80  # leaves room for scrollbar on right
    btn_w = 64
    btn_h = 16
    btn_pad = 12
    ok_btn_x = modal_w // 2 - btn_w - btn_pad//2
    cancel_btn_x = modal_w // 2 + btn_pad//2
    btn_y = modal_h - btn_h - 18

    scrollable = len(rom_files) > max_visible
    scroll_idx = 0
    selected = None
    hover_idx = None
    running = True
    ok_hover = False
    cancel_hover = False
    close_hover = False
    dragging = False
    drag_offset = 0

    clock = pygame.time.Clock()
    while running:
        mx, my = pygame.mouse.get_pos()
        mx = mx // scale - x
        my = my // scale - y

        # -- Which file row is hovered? --
        hover_idx = None
        if list_x <= mx <= list_x + list_w and list_y <= my < list_y + max_visible * row_h:
            idx = (my - list_y) // row_h + scroll_idx
            if 0 <= idx < len(rom_files):
                hover_idx = idx

        # -- Hover for OK/Cancel --
        ok_btn_rect = pygame.Rect(ok_btn_x, btn_y, btn_w, btn_h)
        cancel_btn_rect = pygame.Rect(cancel_btn_x, btn_y, btn_w, btn_h)
        close_btn_rect = pygame.Rect(modal_w-20, 4, 12, 12)

        ok_hover = ok_btn_rect.collidepoint(mx, my)
        cancel_hover = cancel_btn_rect.collidepoint(mx, my)
        close_hover = close_btn_rect.collidepoint(mx, my)

        # -- Scroll bar logic --
        sb_w = scroll_bar_img.get_width()   # Should be 5
        sb_x = modal_w - sb_w               # THIS makes it flush with the popup window's right edge
        sb_y = list_y
        sb_h = scroll_h

        sb_rect = pygame.Rect(sb_x, sb_y, sb_w, sb_h)

        # Scroll thumb logic (unchanged except for width)
        thumb_h = max(16, int(scroll_h * max_visible / len(rom_files))) if scrollable else 0
        max_scroll = len(rom_files) - max_visible if scrollable else 0
        thumb_y = sb_y + int(scroll_idx / max(1, max_scroll) * (sb_h - thumb_h)) if scrollable else sb_y
        thumb_rect = pygame.Rect(sb_x, thumb_y, sb_w, thumb_h)

        # --- Draw modal ---
        # 1. Dim the background
        overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0,0,0, 140))
        screen.blit(overlay, (0,0))

        # 2. Popup window
        modal_surface = pygame.Surface((modal_w, modal_h), pygame.SRCALPHA)
        draw_9slice(modal_surface, 0, 0, modal_w, modal_h, popup_img)
        # 3. Header
        draw_3slice_h(modal_surface, 0, 0, modal_w, header_img, 8, 8)
        # Centered header in modal
        header_label = "Select a ROM file"
        
        text_w = get_text_width(header_label, font_img, font_cmap, 1)
        text_x = (modal_w - text_w) // 2
        draw_text(modal_surface, "Select a ROM file", 105, 0, font_img, font_cmap, color=(255,224,128), scale=1)
        # 4. Close button
        close_state = 1 if close_hover else 0
        modal_surface.blit(close_btn_img.subsurface((close_state*12,0,12,12)), (modal_w-20,4))

        # 5. File list + highlight + selection
        for i in range(max_visible):
            idx = i + scroll_idx
            if idx >= len(rom_files): break
            yrow = list_y + i * row_h
            highlight_x = 16
            highlight_w = modal_w - 32
            highlight_y = yrow - 1
            highlight_h = row_h - 2
            if idx == selected:
                pygame.draw.rect(modal_surface, (40,70,140), (highlight_x, highlight_y, highlight_w, highlight_h), border_radius=5)
            elif idx == hover_idx:
                pygame.draw.rect(modal_surface, (32,40,80), (highlight_x, highlight_y, highlight_w, highlight_h), border_radius=5)

            draw_text(modal_surface, rom_files[idx], highlight_x + 6, yrow, font_regular_img, font_regular_cmap, color=(255,255,255), scale=1)
        # 6. Scroll bar (if needed)
        if scrollable:
            # Draw scroll bar background, edge to edge
            draw_3slice_v(modal_surface, sb_x, sb_y, sb_h, scroll_bar_img, tsize=8, bsize=8)
            # Draw scroll handle/position with correct height and position
            draw_3slice_v(modal_surface, thumb_rect.x, thumb_rect.y, thumb_rect.height, scroll_pos_img, tsize=8, bsize=8)
        # 7. Divider
        divider_y = list_y + max_visible * row_h + 2
        modal_surface.blit(pygame.transform.scale(divider_img, (modal_w-32, 2)), (16, divider_y))
        # --- Calculate button widths and positions based on "Cancel" text ---
        ok_text = "OK"
        cancel_text = "Cancel"
        font_scale = 1
        btn_padding = 12

        # Measure "Cancel" text for button width
        cancel_text_w = get_text_width(cancel_text, font_img, font_cmap, font_scale)
        btn_w = cancel_text_w + btn_padding*2
        gap = 16  # space between buttons

        # Center both buttons at the bottom
        total_w = btn_w * 2 + gap
        ok_btn_x = (modal_w - total_w) // 2
        cancel_btn_x = ok_btn_x + btn_w + gap
        
        # Place buttons a fixed margin above the bottom of the modal window
        btn_margin_bottom = 24  # (or whatever margin you want)
        btn_y = divider_y + divider_gap

        # Calculate vertical centering for button text
        btn_text_y = btn_y + (16 - font_img.get_height() * font_scale) // 2

        # 8. OK and Cancel buttons
        ok_state = 2 if ok_hover and selected is not None else 0
        ok_disabled = (selected is None)
        if ok_disabled:
            draw_3slice_button(modal_surface, ok_btn_x, btn_y, btn_w, std_btn_img, 0)  # always use idle state when grayed
            overlay = pygame.Surface((btn_w, 16), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 0))  # transparent background
            pygame.draw.rect(overlay, (100, 100, 100, 140), overlay.get_rect(), border_radius=2)
            modal_surface.blit(overlay, (ok_btn_x, btn_y))
        else:
            draw_3slice_button(modal_surface, ok_btn_x, btn_y, btn_w, std_btn_img, ok_state)

        draw_text(
            modal_surface, ok_text,
            ok_btn_x + (btn_w - get_text_width(ok_text, font_img, font_cmap, font_scale)) // 2,
            btn_text_y,
            font_img, font_cmap,
            color=(180,180,180) if ok_disabled else (255,255,255), scale=font_scale
        )

        # --- Cancel Button ---
        cancel_state = 2 if cancel_hover else 0
        draw_3slice_button(modal_surface, cancel_btn_x, btn_y, btn_w, std_btn_img, cancel_state)

        # Center and draw Cancel text on button
        draw_text(
            modal_surface, cancel_text,
            cancel_btn_x + (btn_w - get_text_width(cancel_text, font_img, font_cmap, font_scale)) // 2,
            btn_text_y,
            font_img, font_cmap,
            color=(255,255,255), scale=font_scale
        )
        
        # 9. Blit modal to screen
        screen.blit(pygame.transform.scale(modal_surface, (modal_w*scale, modal_h*scale)), (x*scale, y*scale))
        pygame.display.flip()
        
        # --- Event handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                mx = mx // scale - x
                my = my // scale - y
                if close_btn_rect.collidepoint(mx, my):
                    return None
                if ok_btn_rect.collidepoint(mx, my) and selected is not None:
                    return rom_files[selected]
                if cancel_btn_rect.collidepoint(mx, my):
                    return None
                # Scroll thumb drag
                if scrollable and thumb_rect.collidepoint(mx, my):
                    dragging = True
                    drag_offset = my - thumb_rect.y
                # Row selection
                if hover_idx is not None:
                    if event.button == 1:
                        if selected == hover_idx:
                            return rom_files[selected]  # Double click (second click)
                        selected = hover_idx
            elif event.type == pygame.MOUSEBUTTONUP:
                dragging = False
            elif event.type == pygame.MOUSEMOTION and dragging and scrollable:
                my = event.pos[1] // scale - y
                # Clamp mouse Y to scrollable region
                my = max(sb_y + thumb_h//2, min(sb_y + sb_h - thumb_h//2, my))
                rel = (my - sb_y - thumb_h//2) / (sb_h - thumb_h)
                scroll_idx = int(round(rel * max_scroll))
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                elif event.key == pygame.K_DOWN:
                    if selected is None:
                        selected = scroll_idx
                    elif selected < len(rom_files) - 1:
                        selected += 1
                        if selected >= scroll_idx + max_visible:
                            scroll_idx = min(scroll_idx+1, max_scroll)
                    hover_idx = selected
                elif event.key == pygame.K_UP:
                    if selected is None:
                        selected = scroll_idx
                    elif selected > 0:
                        selected -= 1
                        if selected < scroll_idx:
                            scroll_idx = max(selected, 0)
                    hover_idx = selected
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    if selected is not None:
                        return rom_files[selected]
                elif event.key == pygame.K_PAGEUP and scrollable:
                    scroll_idx = max(scroll_idx-max_visible, 0)
                elif event.key == pygame.K_PAGEDOWN and scrollable:
                    scroll_idx = min(scroll_idx+max_visible, max_scroll)
            elif event.type == pygame.MOUSEWHEEL and scrollable:
                if event.y < 0 and scroll_idx < max_scroll:
                    scroll_idx = min(scroll_idx+1, max_scroll)
                elif event.y > 0 and scroll_idx > 0:
                    scroll_idx = max(scroll_idx-1, 0)
        if dragging and scrollable:
            mx, my = pygame.mouse.get_pos()
            my = my // scale - y
            rel = (my - sb_y - thumb_h//2) / (sb_h - thumb_h)
            scroll_idx = int(round(rel * max_scroll))
            scroll_idx = max(0, min(scroll_idx, max_scroll))
        clock.tick(60)

def show_modal_message(screen, popup_img, header_img, font_img, font_cmap, message):
    # Simple message-only modal (for no ROM files)
    scale = SCALE
    modal_w, modal_h = 320, 120
    x = (screen.get_width() // scale - modal_w) // 2
    y = (screen.get_height() // scale - modal_h) // 2
    modal_surface = pygame.Surface((modal_w, modal_h), pygame.SRCALPHA)
    draw_9slice(modal_surface, 0, 0, modal_w, modal_h, popup_img)
    draw_3slice_h(modal_surface, 0, 0, modal_w, header_img, 8, 8)
    draw_text(modal_surface, "No ROM Files", 16, 2, font_img, font_cmap, color=(255,128,128), scale=1)
    draw_text(modal_surface, message, 16, 40, font_img, font_cmap, color=(255,255,255), scale=1)
    overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
    overlay.fill((0,0,0, 140))
    screen.blit(overlay, (0,0))
    screen.blit(pygame.transform.scale(modal_surface, (modal_w*scale, modal_h*scale)), (x*scale, y*scale))
    pygame.display.flip()
    # Wait for ESC or click
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                waiting = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                waiting = False
        pygame.time.wait(20)

# --- Main ---
def main():
    # (Your original pygame.init() and setup code starts here, as before)
    pygame.init()
    real_screen = pygame.display.set_mode((SCREEN_W * SCALE, SCREEN_H * SCALE))
    pygame.display.set_caption("SubpixelDepths - ROM Analyzer")
    clock = pygame.time.Clock()
    screen = pygame.Surface((SCREEN_W, SCREEN_H))  # <— “virtual” 1x surface, we draw to this!

    # Load Assets
    font_bold_img, font_bold_cmap = load_bitmap_font(FONT_FILE, FONT_MAP)
    font_regular_img, font_regular_cmap = load_bitmap_font(FONT_REGULAR_FILE, FONT_REGULAR_MAP)
    btn_full_img = pygame.image.load(BTN_IMAGE).convert_alpha()
    btn_imgs = []
    for i in range(3):
        # Each state is a 1x 56x56 region (from left to right)
        btn_state_img = btn_full_img.subsurface(pygame.Rect(i * 56, 0, 56, 56)).copy()
        btn_imgs.append(btn_state_img)

    logo_img = pygame.image.load(LOGO_IMAGE).convert_alpha()
    # --- Sound Effects ---
    SFX_MENU = pygame.mixer.Sound(asset_path("sfx_menu_selection.wav"))


    # --- Button Data ---
    btn_labels = ["New Project", "Load Project", "Preferences", "Exit"]
    btns = []
    bx = MARGIN_X
    # --- Button Placement (pixel-perfect, mockup style) ---
    btns = []
    # Top margin below title/version, at 1x coordinates
    BTN_TOP = 68      # y-position of first button (adjust to align under version text)
    BTN_GAP = 12      # vertical space between buttons (adjust to taste)
    for i, label in enumerate(btn_labels):
        btns.append({
            "label": label,
            "rect": pygame.Rect(
                MARGIN_X, 
                BTN_TOP + i * (BTN_HEIGHT + BTN_GAP), 
                BTN_WIDTH, 
                BTN_HEIGHT
            )
        })

    # --- Compute logo position ---
    btn_right = bx + BTN_WIDTH // SCALE
    logo_draw_w = logo_img.get_width()
    logo_draw_h = logo_img.get_height()
    logo_center_x = btn_right + (SCREEN_W - btn_right) // 2
    logo_center_y = SCREEN_H // 2
    logo_draw_x = logo_center_x - logo_draw_w // 2
    logo_draw_y = logo_center_y - logo_draw_h // 2

    # --- UI Loop ---
    running = True
    hovered_btn = None
    mouse_down = False
    click_sfx_played = False
    pending_exit = False
    exit_trigger_time = None

    while running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_pos = (mouse_pos[0] // SCALE, mouse_pos[1] // SCALE)
        mouse_clicked = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_down = True
                mouse_clicked = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_down = False
                click_sfx_played = False

        screen.fill((0, 0, 0))
        # Draw logo at 2x (ONLY the logo!)
        logo_2x = pygame.transform.scale(logo_img, (logo_img.get_width()*2, logo_img.get_height()*2))
        logo_draw_w = logo_2x.get_width()
        logo_draw_h = logo_2x.get_height()
        logo_center_x = btn_right + (SCREEN_W - btn_right) // 2
        logo_center_y = SCREEN_H // 2
        logo_draw_x = logo_center_x - logo_draw_w // 2 +32
        logo_draw_y = logo_center_y - logo_draw_h // 2
        screen.blit(
            logo_2x,
            (logo_draw_x, logo_draw_y)
        )
        # Title at 2x, tight to top
        TITLE_Y = 7     # tweak to match mockup
        draw_text(
            screen, TITLE,
            MARGIN_X, TITLE_Y,
            font_bold_img, font_bold_cmap,
            color=(128,192,255), scale=2
        )
        # Version at 1x, 6px below title (tweak as needed)
        VERSION_Y = TITLE_Y + font_bold_img.get_height() * 2 + 3
        draw_text(
            screen, VERSION,
            MARGIN_X, VERSION_Y,
            font_regular_img, font_regular_cmap,
            color=(255,224,128), scale=1
        )

        hovered_btn = None
        for btn in btns:
            bx, by, bw, bh = btn["rect"]
            is_hover = btn["rect"].collidepoint(mouse_pos)
            is_down = is_hover and mouse_down
            if is_hover:
                hovered_btn = btn

            if is_down:
                btn_state = 2  # Click
            elif is_hover:
                btn_state = 1  # Hover
            else:
                btn_state = 0  # Idle

            # Draw at 1x, on the 1x screen!
            draw_9slice_button(
                screen, bx, by, bw, bh, btn_imgs[btn_state], scale=1
            )

            # Center label (still 1x)
            label_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
            draw_text(
                label_surf, btn["label"],
                (bw - get_text_width(btn["label"], font_bold_img, font_bold_cmap, BTN_LABEL_SCALE)) // 2,
                (bh - font_bold_img.get_height() * BTN_LABEL_SCALE) // 2,
                font_bold_img, font_bold_cmap,
                color=(255,255,255), scale=BTN_LABEL_SCALE
            )
            screen.blit(label_surf, (bx, by))

        # On click
        if hovered_btn and mouse_clicked and not click_sfx_played:
            SFX_MENU.play()
            click_sfx_played = True
            if hovered_btn["label"] == "Exit":
                pending_exit = True
                exit_trigger_time = pygame.time.get_ticks()
            elif hovered_btn["label"] == "New Project":
                rom_path = pick_rom_file_modal(real_screen, font_bold_img, font_bold_cmap, font_regular_img, font_regular_cmap)
                if rom_path:
                    dashboard_screen(
                        real_screen, font_bold_img, font_bold_cmap,
                        font_regular_img, font_regular_cmap,
                        os.path.basename(rom_path)
                    )
                    running = False

        # If waiting to exit, check timer
        if pending_exit:
            now = pygame.time.get_ticks()
            # SFX_MENU.get_length() is in seconds, so multiply by 900 for ms
            if now - exit_trigger_time >= int(SFX_MENU.get_length() * 900):
                running = False

        # Scale up the 1x screen to real window size
        real_screen.blit(pygame.transform.scale(screen, (SCREEN_W*SCALE, SCREEN_H*SCALE)), (0,0))
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

def dashboard_screen(real_screen, font_bold_img, font_bold_cmap, font_regular_img, font_regular_cmap, rom_filename):
    clock = pygame.time.Clock()
    dashboard_running = True

    # --- Create a new virtual 1x surface for dashboard drawing ---
    screen = pygame.Surface((SCREEN_W, SCREEN_H))  # 1x pixel buffer

    # Asset loads ...
    def asset_path(filename):
        return os.path.join("Elements", filename)
    header_img = pygame.image.load(asset_path("shell_header_3slice.png")).convert_alpha()
    shell_main_img = pygame.image.load(asset_path("shell_main_9slice.png")).convert_alpha()
    header_icon = pygame.image.load(asset_path("icon_header_dashboard.png")).convert_alpha()
    shade_side = pygame.image.load(asset_path("shell_headershadesides.png")).convert_alpha()
    panel_tray = pygame.image.load(asset_path("panel_traymenu_3slice.png")).convert_alpha()
    box_embed = pygame.image.load(asset_path("box_embeddedtext_3slice.png")).convert_alpha()
    pb_bar = pygame.image.load(asset_path("system_progressbar_bar_3slice.png")).convert_alpha()
    btn_win_min = pygame.image.load(asset_path("button_shell_minimize_3state.png")).convert_alpha()
    btn_win_max = pygame.image.load(asset_path("button_shell_maximize_3state.png")).convert_alpha()
    btn_win_exit = pygame.image.load(asset_path("button_shell_exit_3state.png")).convert_alpha()

    while dashboard_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                dashboard_running = False

        # 1x graphics draw
        screen.fill((24,24,32))
        # ... (everything else stays the same in here)
        # -- everything after this line stays the same as before --
        shell_rect = pygame.Rect(8, 32, SCREEN_W - 16, SCREEN_H - 64)
        screen.blit(
            pygame.transform.scale(shell_main_img, (shell_rect.width, shell_rect.height)),
            shell_rect.topleft
        )

        # --- 3-slice Header ---
        HEADER_L = 45
        HEADER_M = 32
        HEADER_R = 13
        hdr_h = header_img.get_height()
        sw = SCREEN_W
        # Left
        screen.blit(header_img.subsurface((0,0,HEADER_L,hdr_h)), (0,0))
        # Middle
        screen.blit(
            pygame.transform.scale(header_img.subsurface((HEADER_L,0,HEADER_M,hdr_h)), (sw-HEADER_L-HEADER_R, hdr_h)),
            (HEADER_L, 0)
        )
        # Right
        screen.blit(header_img.subsurface((HEADER_L+HEADER_M,0,HEADER_R,hdr_h)), (sw-HEADER_R,0))

        # Header shades at 1x
        screen.blit(shade_side, (0, hdr_h))
        screen.blit(pygame.transform.flip(shade_side, True, False), (SCREEN_W - shade_side.get_width(), hdr_h))

        # -- Header icon and text (1x native, then scaled at end) --
        DASH_SCALE = 1
        REG_SCALE = 1
        # Icon
        icon_w, icon_h = header_icon.get_width(), header_icon.get_height()
        icon_x = (HEADER_L - icon_w) // 2
        icon_y = (hdr_h - icon_h) // 2
        screen.blit(header_icon, (icon_x, icon_y))
        text_x = HEADER_L + 12  # 12px padding after left slice
        text_y = ((hdr_h - font_bold_img.get_height() * DASH_SCALE) // 2) - 1

        # "Dashboard" (1x, will be scaled by the virtual screen)
        draw_text(
            screen, "Dashboard",
            text_x - 6, text_y,
            font_bold_img, font_bold_cmap,
            color=(128,192,255), scale=1
        )
        text_x += get_text_width("Dashboard", font_bold_img, font_bold_cmap, DASH_SCALE) + 10

        # "|" (3x)
        draw_text(
            screen, "|",
            text_x - 6, text_y,
            font_bold_img, font_bold_cmap,
            color=(255,255,255), scale=1
        )
        text_x += get_text_width("|", font_bold_img, font_bold_cmap, DASH_SCALE) + 10

        # "ROM:" (gold, regular, 3x)
        draw_text(
            screen, "ROM:",
            text_x -6 , text_y + 4,
            font_regular_img, font_regular_cmap,
            color=(255,224,128), scale=1
        )
        text_x += get_text_width("ROM:", font_regular_img, font_regular_cmap, REG_SCALE) + 4

        # File name (white, regular, 3x)
        draw_text(
            screen, rom_filename,
            text_x - 6, text_y + 4,
            font_regular_img, font_regular_cmap,
            color=(255,255,255), scale=1
        )

        # --- Notices button ---
        notices_btn_img = pygame.image.load(asset_path("button_standard_3state.png")).convert_alpha()
        notice_icon = pygame.image.load(asset_path("icon_system_warning.png")).convert_alpha()
        NOTICES_BTN_W = 53
        NOTICES_BTN_H = 16
        notices_btn_x = SCREEN_W - 130  # Position from right
        notices_btn_y = 12
        draw_3slice_button(screen, notices_btn_x, notices_btn_y, NOTICES_BTN_W, notices_btn_img, state=0)
        # Icon
        icon_size = notice_icon.get_height()
        screen.blit(notice_icon, (notices_btn_x + 7, notices_btn_y + (NOTICES_BTN_H - icon_size)//2 + 1))
        # Number
        draw_text(
            screen, "(x1)",
            notices_btn_x + 7 + icon_size + 5, notices_btn_y + (NOTICES_BTN_H - font_regular_img.get_height()) // 2 +2,
            font_regular_img, font_regular_cmap,
            color=(255,224,128), scale=1
        )

        # Tray menu (bottom left, 1x)
        screen.blit(panel_tray, (10, SCREEN_H - panel_tray.get_height() - 12))

        # Embedded info bar (bottom)
        embed_y = SCREEN_H - box_embed.get_height() - 4
        screen.blit(pygame.transform.scale(box_embed, (SCREEN_W - 16, box_embed.get_height())), (8, embed_y))
        draw_text(screen, "23% Confirmed", 20, embed_y + 4, font_regular_img, font_regular_cmap, color=(128,255,128), scale=1)
        draw_text(screen, "|", 90, embed_y + 4, font_regular_img, font_regular_cmap, color=(255,255,255), scale=1)
        draw_text(screen, "45% Uncertain", 110, embed_y + 4, font_regular_img, font_regular_cmap, color=(255,224,128), scale=1)
        draw_text(screen, "|", 200, embed_y + 4, font_regular_img, font_regular_cmap, color=(255,255,255), scale=1)
        draw_text(screen, "32% Unidentified", 220, embed_y + 4, font_regular_img, font_regular_cmap, color=(255,64,64), scale=1)

        # Progress Bar (bottom right)
        pb_x = SCREEN_W - 106 - 12
        pb_y = SCREEN_H - 32
        screen.blit(pb_bar, (pb_x, pb_y))

        real_screen.blit(pygame.transform.scale(screen, (SCREEN_W*SCALE, SCREEN_H*SCALE)), (0,0))
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()