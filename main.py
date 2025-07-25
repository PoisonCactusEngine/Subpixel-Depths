from core.assets import (
    asset_path, load_bitmap_font,
    FONT_FILE, FONT_MAP,
    FONT_REGULAR_FILE, FONT_REGULAR_MAP,
    BTN_IMAGE, LOGO_IMAGE
)
from ui.elements import (
    draw_text, draw_9slice, draw_9slice_button, draw_3slice_h,
    draw_3slice_button, draw_3slice_v, get_text_width
)
import pygame
import json
import os
import sys
import subprocess
import time

def update_window_size():
    from core.config import SCALE
    from core.assets import SCREEN_W, SCREEN_H
    window_size = (SCREEN_W * SCALE, SCREEN_H * SCALE)
    return pygame.display.set_mode(window_size, pygame.RESIZABLE)

# --- Settings ---
SCREEN_W, SCREEN_H = 480, 270     # Native resolution
from core.config import SCALE
scale = SCALE
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
    modal_w, modal_h = 320, 200  # Always 1x
    # Center in virtual 1x coordinates
    x = (screen.get_width() // SCALE - modal_w) // 2
    y = (screen.get_height() // SCALE - modal_h) // 2
    modal_rect = pygame.Rect(x, y, modal_w, modal_h)

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
        mx = mx // SCALE - x
        my = my // SCALE - y

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
        real_w, real_h = screen.get_size()
        upscale_modal = pygame.transform.scale(modal_surface, (modal_w * SCALE, modal_h * SCALE))
        real_x = x * SCALE
        real_y = y * SCALE
        screen.blit(upscale_modal, (real_x, real_y))
        pygame.display.flip()
        
        # --- Event handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                real_w, real_h = screen.get_size()
                surf_w, surf_h = SCREEN_W * SCALE, SCREEN_H * SCALE
                offset_x = (real_w - surf_w) // 2
                offset_y = (real_h - surf_h) // 2
                mx = (mx - offset_x) // SCALE - x
                my = (my - offset_y) // SCALE - y
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
                my = event.pos[1] // SCALE - y
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
            my = my // SCALE - y
            rel = (my - sb_y - thumb_h//2) / (sb_h - thumb_h)
            scroll_idx = int(round(rel * max_scroll))
            scroll_idx = max(0, min(scroll_idx, max_scroll))
        clock.tick(60)

def show_modal_message(screen, popup_img, header_img, font_img, font_cmap, message):
    # Simple message-only modal (for no ROM files)
    scale = SCALE
    modal_w, modal_h = 320, 120
    x = (screen.get_width() // SCALE - modal_w) // 2
    y = (screen.get_height() // SCALE - modal_h) // 2
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
import os
import sys
import pygame
from core.assets import SCREEN_W, SCREEN_H, SCALE
from screens.title import title_screen

# Suppress pygame community message
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

def main():
    pygame.init()
    real_screen = update_window_size()
    pygame.display.set_caption("SubpixelDepths - ROM Analyzer")

    try:
        title_screen(real_screen)
    finally:
        pygame.display.quit()
        pygame.quit()

if __name__ == "__main__":
    main()

def get_best_scale(native_w, native_h):
    info = pygame.display.Info()
    usable_w = info.current_w
    usable_h = info.current_h
    for scale in range(6, 0, -1):
        if native_w * scale <= usable_w and native_h * scale <= usable_h:
            return scale
    return 1

def dashboard_screen(real_screen, font_bold_img, font_bold_cmap, font_regular_img, font_regular_cmap, rom_filename):
    global SCALE
    clock = pygame.time.Clock()
    dashboard_running = True

    # --- Maximization state ---
    dashboard_maximized = False
    prev_window_size = None
    prev_scale = None

    # --- Create a new virtual 1x surface for dashboard drawing ---
    screen = pygame.Surface((SCREEN_W, SCREEN_H))  # 1x pixel buffer

    btn_clicked = None
    # --- Notices Popup Assets ---
    popup_main_img = pygame.image.load(asset_path("popup_main_9slice.png")).convert_alpha()
    close_popup_btn_img = pygame.image.load(asset_path("button_closepopup_3state.png")).convert_alpha()
        
    # --- Notices Popup Assets ---
    popup_main_img = pygame.image.load(asset_path("popup_main_9slice.png")).convert_alpha()
    close_popup_btn_img = pygame.image.load(asset_path("button_closepopup_3state.png")).convert_alpha()

    # --- Notices Popup Assets ---
    popup_main_img = pygame.image.load(asset_path("popup_main_9slice.png")).convert_alpha()
    close_popup_btn_img = pygame.image.load(asset_path("button_closepopup_3state.png")).convert_alpha()
    # --- Notices Popup State ---
    notices_popup_open = False
    notices = [
        "Routine 'Jump' assigned twice to enemy objects.",
        "Object 'Magic Key' is missing animation frames.",
        "Ability 'Wall Slide' has no assigned button."
    ]
    notices_selected = None
    notices_hovered = None
    
    # Asset loads ...
    header_img = pygame.image.load(asset_path("shell_header_3slice.png")).convert_alpha()
    shell_main_img = pygame.image.load(asset_path("shell_main_9slice.png")).convert_alpha()
    header_icon = pygame.image.load(asset_path("icon_header_dashboard.png")).convert_alpha()
    shade_side = pygame.image.load(asset_path("shell_headershadesides.png")).convert_alpha()
    panel_tray = pygame.image.load(asset_path("panel_traymenu_3slice.png")).convert_alpha()
    box_embed = pygame.image.load(asset_path("box_embeddedtext_3slice.png")).convert_alpha()
    pb_bar = pygame.image.load(asset_path("system_progressbar_bar_3slice.png")).convert_alpha()
    btn_win_min = pygame.image.load(asset_path("button_shell_minimize_3state.png")).convert_alpha()
    btn_win_max = pygame.image.load(asset_path("button_shell_maximize_3state.png")).convert_alpha()
    btn_win_windowed = pygame.image.load(asset_path("button_shell_windowed_3state.png")).convert_alpha()
    btn_win_exit = pygame.image.load(asset_path("button_shell_exit_3state.png")).convert_alpha()
    tooltip_img = pygame.image.load(asset_path("popup_tooltips_9slice.png")).convert_alpha()

    # --- Notices Popup State ---
    notices_popup_open = False
    notices = [
        "Routine 'Jump' assigned twice to enemy objects.",
        "Object 'Magic Key' is missing animation frames.",
        "Ability 'Wall Slide' has no assigned button."
    ]
    notices_selected = None
    notices_hovered = None

    # --- Notices Popup Assets ---
    popup_main_img = pygame.image.load(asset_path("popup_main_9slice.png")).convert_alpha()
    close_popup_btn_img = pygame.image.load(asset_path("button_closepopup_3state.png")).convert_alpha()
    # --- Notices Popup State ---
    notices_popup_open = False
    notices = [
        "Routine 'Jump' assigned twice to enemy objects.",
        "Object 'Magic Key' is missing animation frames.",
        "Ability 'Wall Slide' has no assigned button."
    ]
    notices_selected = None
    notices_hovered = None

    # --- Tooltip state ---
    tray_tooltip_labels = [
        "Undo",
        "Redo",
        "Save project",
        "Back to Dashboard",
        "Open Preferences",
        "Show Help"
    ]
    tooltip_timer = 0
    tooltip_idx = -1
    tooltip_active = False
    tooltip_mouse_pos = (0, 0)
    TOOLTIP_DELAY = 380  # ms
    TOOLTIP_DIST = 60    # px (cancel if mouse leaves this area)
        
    while dashboard_running:
        btn_clicked = None  # Reset every frame

        mouse_up = False
        mouse_down = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                dashboard_running = False  # Exit dashboard
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_down = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_up = True
                if win_exit_rect.collidepoint(virt_x, virt_y):
                    btn_clicked = "exit"
                elif win_min_rect.collidepoint(virt_x, virt_y):
                    btn_clicked = "min"
                elif win_max_rect.collidepoint(virt_x, virt_y):
                    btn_clicked = "max"
            # --- Notices Button ---
            if pygame.Rect(notices_btn_x, notices_btn_y, NOTICES_BTN_W, NOTICES_BTN_H).collidepoint(virt_x, virt_y):
                notices_popup_open = True
                notices_selected = None

            # --- NEW: Notices Popup Interactivity ---
            if notices_popup_open:
                # Mouse position in popup coordinates
                POPUP_W, POPUP_H = 240, 110
                POPUP_X = (SCREEN_W - POPUP_W) // 2
                POPUP_Y = (SCREEN_H - POPUP_H) // 2
                CLOSE_BTN_W, CLOSE_BTN_H = 16, 16
                CLOSE_BTN_X = POPUP_X + POPUP_W - CLOSE_BTN_W - 4
                CLOSE_BTN_Y = POPUP_Y + 4
                notice_gap = 18

                mx, my = virt_x, virt_y
                # Close button
                if event.type == pygame.MOUSEBUTTONDOWN and pygame.Rect(CLOSE_BTN_X, CLOSE_BTN_Y, CLOSE_BTN_W, CLOSE_BTN_H).collidepoint(mx, my):
                    notices_popup_open = False
                # Click or hover notices
                for i in range(len(notices)):
                    msg_rect = pygame.Rect(POPUP_X + 16, POPUP_Y + 32 + i * notice_gap, POPUP_W - 32, 16)
                    if msg_rect.collidepoint(mx, my):
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            notices_selected = i
                        elif event.type == pygame.MOUSEMOTION:
                            notices_hovered = i
                # Dismiss on ESC
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    notices_popup_open = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    dashboard_running = False  # Allow escape key to close

        # 1x graphics draw
        screen.fill((24,24,32))

        # Stretch the shell window all the way to the screen edges (behind everything)
        draw_9slice(screen, 0, 0, SCREEN_W, SCREEN_H, shell_main_img, csize=12)

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
        # --- Notices Popup (drawn above everything) ---
        if notices_popup_open:
            POPUP_W, POPUP_H = 240, 110  # You can adjust size as needed
            POPUP_X = (SCREEN_W - POPUP_W) // 2
            POPUP_Y = (SCREEN_H - POPUP_H) // 2

            # Draw 9-slice popup window
            draw_9slice(screen, POPUP_X, POPUP_Y, POPUP_W, POPUP_H, popup_main_img)

            # Draw close 'X' button
            CLOSE_BTN_W, CLOSE_BTN_H = 16, 16
            CLOSE_BTN_X = POPUP_X + POPUP_W - CLOSE_BTN_W - 4
            CLOSE_BTN_Y = POPUP_Y + 4
            mouse_pos_virt = (virt_x, virt_y)
            close_rect = pygame.Rect(CLOSE_BTN_X, CLOSE_BTN_Y, CLOSE_BTN_W, CLOSE_BTN_H)
            close_hover = close_rect.collidepoint(*mouse_pos_virt)
            mouse_buttons = pygame.mouse.get_pressed()
            close_down = close_hover and mouse_buttons[0]

            # Pick button state: 0=idle, 1=hover, 2=click
            if close_down:
                close_state = 2
            elif close_hover:
                close_state = 1
            else:
                close_state = 0

            state_count = close_popup_btn_img.get_width() // 16
            safe_state = max(0, min(close_state, state_count - 1))
            # Only subsurface if valid
            if 0 <= safe_state < state_count:
                screen.blit(close_popup_btn_img.subsurface((safe_state*16, 0, 16, 16)), (CLOSE_BTN_X, CLOSE_BTN_Y))

            # Draw Notices Title
            draw_text(screen, "Notices", POPUP_X + 12, POPUP_Y + 8, font_bold_img, font_bold_cmap, color=(128,192,255), scale=1)

            # Draw notice list with highlight
            notice_y = POPUP_Y + 32
            notice_gap = 18
            for i, msg in enumerate(notices):
                msg_rect = pygame.Rect(POPUP_X + 16, notice_y + i*notice_gap, POPUP_W-32, 16)
                is_hover = msg_rect.collidepoint(*mouse_pos_virt)
                if is_hover:
                    pygame.draw.rect(screen, (60,90,160), msg_rect, border_radius=4)
                if notices_selected == i:
                    pygame.draw.rect(screen, (40,70,130), msg_rect, border_radius=4)
                draw_text(screen, msg, msg_rect.x+4, msg_rect.y+2, font_regular_img, font_regular_cmap, color=(255,255,255), scale=1)

            # Draw Notices Title
            draw_text(screen, "Notices", POPUP_X + 12, POPUP_Y + 8, font_bold_img, font_bold_cmap, color=(128,192,255), scale=1)

            # Draw notice list with highlight
            notice_y = POPUP_Y + 32
            notice_gap = 18
            for i, msg in enumerate(notices):
                msg_rect = pygame.Rect(POPUP_X + 16, notice_y + i*notice_gap, POPUP_W-32, 16)
                is_hover = msg_rect.collidepoint(*mouse_pos_virt)
                if is_hover:
                    pygame.draw.rect(screen, (60,90,160), msg_rect, border_radius=4)
                if notices_selected == i:
                    pygame.draw.rect(screen, (40,70,130), msg_rect, border_radius=4)
                draw_text(screen, msg, msg_rect.x+4, msg_rect.y+2, font_regular_img, font_regular_cmap, color=(255,255,255), scale=1)

        # --- Top-right window buttons (idle/hover/click states, with logic) ---
        WIN_BTN_W, WIN_BTN_H = 17, 16
        WIN_BTN_GAP = 1
        win_btn_y = 12
        win_exit_x = SCREEN_W - WIN_BTN_W - 13
        win_max_x = win_exit_x - WIN_BTN_W - WIN_BTN_GAP
        win_min_x = win_max_x - WIN_BTN_W - WIN_BTN_GAP

        # Track rects for click logic
        win_min_rect = pygame.Rect(win_min_x, win_btn_y, WIN_BTN_W, WIN_BTN_H)
        win_max_rect = pygame.Rect(win_max_x, win_btn_y, WIN_BTN_W, WIN_BTN_H)
        win_exit_rect = pygame.Rect(win_exit_x, win_btn_y, WIN_BTN_W, WIN_BTN_H)
        win_btn_rects = [win_min_rect, win_max_rect, win_exit_rect]

        # --- Get mouse position ONCE per frame ---
        phys_x, phys_y = pygame.mouse.get_pos()
        real_w, real_h = real_screen.get_size()
        surf_w, surf_h = SCREEN_W * SCALE, SCREEN_H * SCALE
        offset_x = (real_w - surf_w) // 2
        offset_y = (real_h - surf_h) // 2
        virt_x = (phys_x - offset_x) // SCALE
        virt_y = (phys_y - offset_y) // SCALE

        # --- Window Button State Logic (hover/click) ---
        mouse_buttons = pygame.mouse.get_pressed()
        is_down = mouse_buttons[0]

        win_btn_states = [0, 0, 0]  # idle by default

        # Only track hover/click in virtual 1x space!
        if win_min_rect.collidepoint(virt_x, virt_y):
            win_btn_states[0] = 2 if is_down else 1
        if win_max_rect.collidepoint(virt_x, virt_y):
            win_btn_states[1] = 2 if is_down else 1
        if win_exit_rect.collidepoint(virt_x, virt_y):
            win_btn_states[2] = 2 if is_down else 1

        # Draw window buttons with proper state
        screen.blit(btn_win_min.subsurface((win_btn_states[0]*WIN_BTN_W,0,WIN_BTN_W,WIN_BTN_H)), (win_min_x, win_btn_y))
        if dashboard_maximized:
            screen.blit(btn_win_windowed.subsurface((win_btn_states[1]*WIN_BTN_W,0,WIN_BTN_W,WIN_BTN_H)), (win_max_x, win_btn_y))
        else:
            screen.blit(btn_win_max.subsurface((win_btn_states[1]*WIN_BTN_W,0,WIN_BTN_W,WIN_BTN_H)), (win_max_x, win_btn_y))
        screen.blit(btn_win_exit.subsurface((win_btn_states[2]*WIN_BTN_W,0,WIN_BTN_W,WIN_BTN_H)), (win_exit_x, win_btn_y))
        
        # Now respond to the click
        if btn_clicked == "exit":
            dashboard_running = False  # Exit dashboard
        elif btn_clicked == "min":
            pygame.display.iconify()
            time.sleep(0.2)
        elif btn_clicked == "max":
            if not dashboard_maximized:
                dashboard_maximized = True
                prev_window_size = real_screen.get_size()
                prev_scale = SCALE
                info = pygame.display.Info()
                # Calculate the best scale for the physical display
                best_scale = 1
                for s in range(8, 0, -1):
                    if SCREEN_W * s <= info.current_w and SCREEN_H * s <= info.current_h:
                        best_scale = s
                        break
                SCALE = best_scale
                pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
                time.sleep(0.25)  # Give the OS a moment to settle
            else:
                dashboard_maximized = False
                # Restore previous scale and window size
                SCALE = prev_scale
                pygame.display.set_mode((SCREEN_W * SCALE, SCREEN_H * SCALE), pygame.RESIZABLE)
                time.sleep(0.25)

        # Embedded info bar (bottom) Stretch the bottom info bar (3-slice, horizontal) across the full width of the screen
        embed_bar_height = box_embed.get_height()
        embed_y = SCREEN_H - embed_bar_height
        draw_3slice_h(screen, 0, embed_y, SCREEN_W, box_embed)
        info_text_y = embed_y + (embed_bar_height - font_regular_img.get_height()) // 2
        draw_text(screen, "23% Confirmed", 150, info_text_y + 2, font_regular_img, font_regular_cmap, color=(128,255,128), scale=1)
        draw_text(screen, "|", 230, info_text_y + 2, font_regular_img, font_regular_cmap, color=(255,255,255), scale=1)
        draw_text(screen, "45% Uncertain", 240, info_text_y + 2, font_regular_img, font_regular_cmap, color=(255,224,128), scale=1)
        draw_text(screen, "|", 320, info_text_y + 2, font_regular_img, font_regular_cmap, color=(255,255,255), scale=1)
        draw_text(screen, "32% Left", 330, info_text_y + 2, font_regular_img, font_regular_cmap, color=(255,64,64), scale=1)

        # Tray menu - Stretch across the left edge (3-slice horizontal)
        tray_height = panel_tray.get_height()
        tray_width = 133  # Or however wide you want the tray menu (try matching the mockup visually)
        tray_y = SCREEN_H - tray_height
        draw_3slice_h(screen, 0, tray_y, tray_width, panel_tray)
        
        # --- Tray icons (6 total, spaced out to fit the tray width) ---
        tray_icons = [
            ("icon_system_main_undo.png",    "sfx_main_undo.wav"),
            ("icon_system_main_redo.png",    "sfx_main_redo.wav"),
            ("icon_system_main_save.png",    "sfx_main_save.wav"),
            ("icon_system_main_backtodashboard.png", "sfx_main_back.wav"),
            ("icon_system_main_preferences.png", "sfx_main_preferences.wav"),
            ("icon_system_main_help.png",    "sfx_main_help.wav"),
        ]

        tray_icon_imgs = [pygame.image.load(asset_path(fname)).convert_alpha() for fname, _ in tray_icons]
        icon_y = tray_y + (tray_height - 12) // 2  # center in tray
        icon_x = 7
        icon_spacing = 21

        # --- Tray Icon Interactivity ---
        tray_icon_rects = []
        highlight_color = (40, 60, 140, 80)
        active_color = (120, 200, 255, 110)
        mx, my = pygame.mouse.get_pos()
        virt_x = (mx - offset_x) // SCALE
        virt_y = (my - offset_y) // SCALE

        tray_hover_idx = -1
        tray_click_idx = -1

        # --- Tray Icon Interactivity & Drawing (Improved Highlight) ---
        tray_icon_clicked = -1  # Track which icon is clicked
        for i, img in enumerate(tray_icon_imgs):
            rect = pygame.Rect(icon_x, icon_y, img.get_width(), img.get_height())
            tray_icon_rects.append(rect)
            hovered = rect.collidepoint(virt_x, virt_y)
            held = hovered and mouse_down

            # Tooltip tracking
            if hovered:
                if tooltip_idx != i:
                    tooltip_idx = i
                    tooltip_timer = pygame.time.get_ticks()
                    tooltip_active = False
                    tooltip_mouse_pos = (mx, my)
                elif not tooltip_active and pygame.time.get_ticks() - tooltip_timer > TOOLTIP_DELAY:
                    tooltip_active = True
                    tooltip_mouse_pos = (mx, my)
            elif tooltip_idx == i:
                # Left the icon; reset tooltip
                tooltip_idx = -1
                tooltip_active = False

            # Draw rounded highlight background
            if held:
                # Bright, solid highlight for click/hold
                color = (170, 235, 255, 140)
                border_radius = 5
            elif hovered:
                # Softer highlight for hover
                color = (70, 110, 180, 80)
                border_radius = 4
            else:
                color = None

            if color:
                hl_surf = pygame.Surface((img.get_width()+4, img.get_height()+4), pygame.SRCALPHA)
                pygame.draw.rect(
                    hl_surf, color, 
                    pygame.Rect(0, 0, img.get_width()+4, img.get_height()+4), 
                    border_radius=border_radius
                )
                screen.blit(hl_surf, (icon_x-2, icon_y-2))

            # Draw the icon itself
            screen.blit(img, (icon_x, icon_y))

            # Play SFX & detect click on release (mouse_up)
            if hovered and mouse_up:
                sfx = pygame.mixer.Sound(asset_path(tray_icons[i][1]))
                sfx.play()
                tray_icon_clicked = i

            icon_x += icon_spacing

        # --- Handle Tray Icon Actions (just print for now) ---
        if tray_icon_clicked != -1:
            # You can add real functionality later
            if tray_icon_clicked == 0:
                print("UNDO")
            elif tray_icon_clicked == 1:
                print("REDO")
            elif tray_icon_clicked == 2:
                print("SAVE")
            elif tray_icon_clicked == 3:
                print("BACK TO DASHBOARD")
            elif tray_icon_clicked == 4:
                print("PREFERENCES")
            elif tray_icon_clicked == 5:
                print("HELP")

        # --- Play SFX on Click (optional: add your sfx logic here) ---
        # e.g. if tray_click_idx != -1:
        #       pygame.mixer.Sound(asset_path(tray_icons[tray_click_idx][1])).play()

        # --- Draw tooltip if needed ---
        if tooltip_active and 0 <= tooltip_idx < len(tray_tooltip_labels):
            tip = tray_tooltip_labels[tooltip_idx]
            padding_x = 8
            padding_y = 6  # vertical space inside the pop
            cs = 8  # 9-slice corner size

            # Get actual text width in pixels
            tip_text_w = get_text_width(tip, font_regular_img, font_regular_cmap, 1, space_px=3)
            tip_w = tip_text_w + padding_x * 2
            tip_h = cs * 2  # Only top + bottom, no vertical stretch!

            mx, my = pygame.mouse.get_pos()
            tip_x = (mx - offset_x) // SCALE - tip_w // 2
            tip_y = (my - offset_y) // SCALE - tip_h - 8  # above mouse

            # Keep inside screen
            tip_x = max(0, min(SCREEN_W - tip_w, tip_x))
            tip_y = max(0, tip_y)

            # --- Top row ---
            TL = tooltip_img.subsurface(pygame.Rect(0,0,cs,cs))
            T  = tooltip_img.subsurface(pygame.Rect(cs,0,tooltip_img.get_width()-2*cs,cs))
            TR = tooltip_img.subsurface(pygame.Rect(tooltip_img.get_width()-cs,0,cs,cs))
            # --- Bottom row ---
            BL = tooltip_img.subsurface(pygame.Rect(0,tooltip_img.get_height()-cs,cs,cs))
            B  = tooltip_img.subsurface(pygame.Rect(cs,tooltip_img.get_height()-cs,tooltip_img.get_width()-2*cs,cs))
            BR = tooltip_img.subsurface(pygame.Rect(tooltip_img.get_width()-cs,tooltip_img.get_height()-cs,cs,cs))

            # Draw top row
            screen.blit(TL, (tip_x, tip_y))
            screen.blit(pygame.transform.scale(T, (tip_w-2*cs, cs)), (tip_x+cs, tip_y))
            screen.blit(TR, (tip_x+tip_w-cs, tip_y))
            # Draw bottom row **immediately below top**
            screen.blit(BL, (tip_x, tip_y+cs))
            screen.blit(pygame.transform.scale(B, (tip_w-2*cs, cs)), (tip_x+cs, tip_y+cs))
            screen.blit(BR, (tip_x+tip_w-cs, tip_y+cs))

            # --- Draw the text perfectly centered in the popup (horizontal & vertical)
            tip_text_x = tip_x + (tip_w - tip_text_w) // 2
            tip_text_y = tip_y + (tip_h - font_regular_img.get_height()) // 2 + 2  # +2 for your desired vertical nudge
            draw_text(
                screen, tip,
                tip_text_x,
                tip_text_y,
                font_regular_img, font_regular_cmap, color=(255,255,255), scale=1
            )

            # Hide tooltip if mouse moves too far
            if abs(mx - tooltip_mouse_pos[0]) > TOOLTIP_DIST or abs(my - tooltip_mouse_pos[1]) > TOOLTIP_DIST:
                tooltip_active = False
                tooltip_idx = -1

        # Progress Bar (bottom right, over tray, use 3-slice)
        pb_bar_w = 106
        pb_bar_h = pb_bar.get_height()
        pb_x = 374
        pb_y = SCREEN_H - 1 - pb_bar_h
        draw_3slice_h(screen, pb_x, pb_y, pb_bar_w, pb_bar)

        # --- Progress Fill: 100px interior for juice ---
        pb_fill_img = pygame.image.load(asset_path("system_progressbar_fills.png")).convert_alpha()
        fill_start = pb_x + 3  # start after left wall (8px left, but 3px inner gap)
        fill_y = pb_y + 2      # adjust as needed

        fill_width = 100       # interior fill width (px)
        # These numbers can be set as variables later!
        confirmed_pct = 0.23
        uncertain_pct = 0.45
        unidentified_pct = 1.0 - confirmed_pct - uncertain_pct

        # Fill colors: 0=green, 1=yellow, 2=red (use slice order in your .png)
        # --- Draw Progress Bar Fill (green and yellow segments, smooth fill) ---
        fill_seg_w = pb_fill_img.get_width() // 3
        fill_seg_h = pb_fill_img.get_height()

        curr_x = fill_start
        # Green fill (Confirmed)
        g_w = min(int(round(fill_width * confirmed_pct)), fill_width)
        if g_w > 0:
            # Always stretch the green fill from its source segment
            green_src = pb_fill_img.subsurface((0, 0, fill_seg_w, fill_seg_h))
            green_scaled = pygame.transform.scale(green_src, (g_w, fill_seg_h))
            screen.blit(green_scaled, (curr_x, fill_y +1))
            curr_x += g_w

        # Yellow fill (Uncertain)
        y_w = min(int(round(fill_width * uncertain_pct)), fill_width - g_w)
        if y_w > 0:
            yellow_src = pb_fill_img.subsurface((fill_seg_w, 0, fill_seg_w, fill_seg_h))
            yellow_scaled = pygame.transform.scale(yellow_src, (y_w, fill_seg_h))
            screen.blit(yellow_scaled, (curr_x, fill_y +1))
            curr_x += y_w

        # Do NOT draw red segment for now (unidentified is just empty)

        # Center the scaled app in the physical window
        real_w, real_h = real_screen.get_size()
        surf_w, surf_h = SCREEN_W * SCALE, SCREEN_H * SCALE
        offset_x = (real_w - surf_w) // 2
        offset_y = (real_h - surf_h) // 2
        real_screen.fill((0,0,0))  # Black bars
        real_screen.blit(pygame.transform.scale(screen, (surf_w, surf_h)), (offset_x, offset_y))
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()