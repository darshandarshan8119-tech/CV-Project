"""Pixora's premium creative-software theme tokens and comprehensive styling.

Features:
- Obsidian Dark and Studio Titanium Light modes with high-contrast, crystal-clear typography.
- Eliminated child widget background inheritance (no unwanted shadow/banding boxes inside blocks).
- Interactive card hover glow effects with corresponding colors (violet, emerald, coral, cyan).
- Pointer cursor feedback on all interactive blocks.
"""
from __future__ import annotations

DARK = {
    # Backgrounds & canvas
    "bg": "#0B0C12",
    "bg_subtle": "#12141F",
    "panel": "#171A27",
    "panel_hi": "#1F2334",
    "panel_hover": "#262C42",
    "raised": "#252B3E",
    "raised_hover": "#2E364E",
    
    # Glassmorphism tokens
    "glass_bg": "rgba(23, 26, 39, 0.90)",
    "glass_border": "rgba(255, 255, 255, 0.08)",
    "glass_border_hi": "rgba(124, 108, 255, 0.45)",
    
    # Text - Crystal clear high contrast
    "text": "#E2E8F0",
    "text_bright": "#FFFFFF",
    "subtext": "#94A3B8",
    "muted": "#717D96",
    "line": "#262D42",
    "line_subtle": "#1C2030",
    
    # Accents & Glows
    "accent": "#7C6CFF",
    "accent_hi": "#9487FF",
    "accent_deep": "#5B4AE0",
    "accent_glow": "#7C6CFF",
    "accent_light": "rgba(124, 108, 255, 0.16)",
    
    # Status / Functional Colors
    "success": "#10B981",
    "success_glow": "#10B981",
    "success_bg": "rgba(16, 185, 129, 0.14)",
    "warning": "#F59E0B",
    "warning_glow": "#F59E0B",
    "danger": "#FB7185",
    "danger_glow": "#FB7185",
    "info": "#06B6D4",
    "info_glow": "#06B6D4",
    
    "shadow_sm": "rgba(0, 0, 0, 0.4)",
    "shadow_lg": "rgba(0, 0, 0, 0.65)",
}

LIGHT = {
    # Backgrounds & canvas
    "bg": "#F4F6FB",
    "bg_subtle": "#EAEDF5",
    "panel": "#FFFFFF",
    "panel_hi": "#F8FAFD",
    "panel_hover": "#F0F4FA",
    "raised": "#EDF1F7",
    "raised_hover": "#E2E7F0",
    
    # Glassmorphism tokens
    "glass_bg": "rgba(255, 255, 255, 0.96)",
    "glass_border": "rgba(0, 0, 0, 0.08)",
    "glass_border_hi": "rgba(99, 85, 255, 0.35)",
    
    # Text - Deep rich slate for maximum readability on white
    "text": "#1E293B",
    "text_bright": "#0F172A",
    "subtext": "#475569",
    "muted": "#64748B",
    "line": "#DDE3ED",
    "line_subtle": "#EEF2F6",
    
    # Accents & Glows
    "accent": "#6355FF",
    "accent_hi": "#5143EE",
    "accent_deep": "#4031D4",
    "accent_glow": "#6355FF",
    "accent_light": "rgba(99, 85, 255, 0.12)",
    
    # Status / Functional Colors
    "success": "#059669",
    "success_glow": "#059669",
    "success_bg": "rgba(5, 150, 105, 0.12)",
    "warning": "#D97706",
    "warning_glow": "#D97706",
    "danger": "#E11D48",
    "danger_glow": "#E11D48",
    "info": "#0891B2",
    "info_glow": "#0891B2",
    
    "shadow_sm": "rgba(0, 0, 0, 0.06)",
    "shadow_lg": "rgba(0, 0, 0, 0.12)",
}


def stylesheet(c: dict) -> str:
    """Generate high-fidelity desktop stylesheet with crystal-clear visibility and no child ghosting."""
    return f"""
    * {{
        font-family: 'Segoe UI', -apple-system, 'SF Pro Display', BlinkMacSystemFont, Roboto, sans-serif;
        font-size: 13px;
        color: {c['text']};
        outline: none;
    }}

    QMainWindow {{
        background: {c['bg']};
    }}

    /* Prevent QWidget background from leaking into child labels / layout items */
    QWidget {{
        color: {c['text']};
    }}

    QLabel {{
        background: transparent;
        color: {c['text']};
    }}

    QScrollArea {{
        background: transparent;
        border: none;
    }}

    QScrollArea > QWidget > QWidget {{
        background: transparent;
    }}

    /* =========================================================================
       SIDEBAR & NAVIGATION
       ========================================================================= */
    QFrame#sidebar {{
        background: {c['panel']};
        border-right: 1px solid {c['line']};
    }}

    QLabel#brand {{
        font-size: 21px;
        font-weight: 800;
        letter-spacing: 2px;
        color: {c['text_bright']};
    }}

    QLabel#section {{
        color: {c['muted']};
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }}

    /* =========================================================================
       CARDS & BLOCKS (With clean corresponding hover glow effects)
       ========================================================================= */
    QFrame#card {{
        background: {c['panel']};
        border: 1px solid {c['line']};
        border-radius: 12px;
    }}

    QFrame#card:hover {{
        border: 1.5px solid {c['accent_hi']};
        background: {c['panel_hi']};
    }}

    QFrame#card[glow="emerald"]:hover {{
        border: 1.5px solid {c['success']};
    }}

    QFrame#card[glow="coral"]:hover {{
        border: 1.5px solid {c['danger']};
    }}

    QFrame#card[glow="cyan"]:hover {{
        border: 1.5px solid {c['info']};
    }}

    QFrame#featureCard {{
        background: {c['panel_hi']};
        border: 1.5px solid {c['line']};
        border-radius: 14px;
    }}

    QFrame#featureCard:hover {{
        border: 1.5px solid {c['accent']};
    }}

    QFrame#featureCard[glow="emerald"]:hover {{
        border: 1.5px solid {c['success']};
    }}

    QFrame#featureCard[glow="coral"]:hover {{
        border: 1.5px solid {c['danger']};
    }}

    QFrame#glassPanel {{
        background: {c['glass_bg']};
        border: 1px solid {c['glass_border']};
        border-radius: 12px;
    }}

    /* Child widgets inside cards must have transparent background to prevent banding */
    QFrame#card QWidget, QFrame#featureCard QWidget, QFrame#glassPanel QWidget {{
        background: transparent;
    }}

    /* =========================================================================
       TYPOGRAPHY HIERARCHY (Ensures crisp contrast in both Dark and Light)
       ========================================================================= */
    QLabel#pageTitle {{
        font-size: 24px;
        font-weight: 700;
        color: {c['text_bright']};
        letter-spacing: -0.3px;
    }}

    QLabel#cardTitle {{
        font-size: 15px;
        font-weight: 700;
        color: {c['text_bright']};
    }}

    QLabel#pageSub {{
        color: {c['subtext']};
        font-size: 13px;
        line-height: 1.4;
    }}

    QLabel#muted {{
        color: {c['muted']};
        font-size: 12px;
    }}

    QLabel#metric {{
        font-size: 32px;
        font-weight: 800;
        color: {c['text_bright']};
        letter-spacing: -0.5px;
    }}

    QLabel#metricLabel {{
        color: {c['muted']};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
    }}

    /* Badges & Pills */
    QLabel#pill {{
        background: {c['raised']};
        color: {c['text']};
        border: 1px solid {c['line']};
        border-radius: 12px;
        padding: 4px 10px;
        font-size: 11px;
        font-weight: 600;
    }}

    QLabel#pillActive {{
        background: {c['accent_light']};
        color: {c['accent_hi']};
        border: 1px solid {c['accent']};
        border-radius: 12px;
        padding: 4px 10px;
        font-size: 11px;
        font-weight: 700;
    }}

    QLabel#pillSuccess {{
        background: {c['success_bg']};
        color: {c['success']};
        border: 1px solid {c['success']};
        border-radius: 12px;
        padding: 4px 10px;
        font-size: 11px;
        font-weight: 700;
    }}

    /* =========================================================================
       BUTTONS (Clear hover glow & active states)
       ========================================================================= */
    QPushButton {{
        background: {c['raised']};
        color: {c['text']};
        border: 1px solid {c['line']};
        border-radius: 8px;
        padding: 8px 14px;
        font-weight: 600;
        font-size: 12px;
        text-align: center;
        min-height: 18px;
    }}

    QPushButton:hover {{
        background: {c['raised_hover']};
        border: 1px solid {c['accent']};
        color: {c['text_bright']};
    }}

    QPushButton:pressed {{
        background: {c['panel_hi']};
        border: 1px solid {c['accent_deep']};
    }}

    QPushButton:disabled {{
        background: {c['panel']};
        border: 1px solid {c['line_subtle']};
        color: {c['muted']};
        opacity: 0.5;
    }}

    QPushButton#primary {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {c['accent']}, stop:1 {c['accent_deep']});
        color: #FFFFFF;
        font-weight: 700;
        border: 1px solid {c['accent_hi']};
        border-radius: 8px;
        padding: 9px 18px;
    }}

    QPushButton#primary:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {c['accent_hi']}, stop:1 {c['accent']});
        border: 1.5px solid #FFFFFF;
    }}

    QPushButton#primary:pressed {{
        background: {c['accent_deep']};
        border: 1px solid {c['accent']};
    }}

    QPushButton#secondary {{
        background: {c['raised']};
        color: {c['text']};
        border: 1px solid {c['line']};
        font-weight: 600;
        border-radius: 8px;
        padding: 8px 14px;
    }}

    QPushButton#secondary:hover {{
        background: {c['raised_hover']};
        color: {c['text_bright']};
        border: 1px solid {c['accent']};
    }}

    QPushButton#navButton {{
        background: transparent;
        color: {c['subtext']};
        border: none;
        border-radius: 8px;
        padding: 9px 14px;
        text-align: left;
        font-size: 13px;
        font-weight: 500;
    }}

    QPushButton#navButton:hover {{
        background: {c['raised']};
        color: {c['text_bright']};
    }}

    QPushButton#navActive {{
        background: {c['accent_light']};
        color: {c['accent_hi']};
        font-weight: 700;
        border-left: 3px solid {c['accent']};
        border-radius: 0 8px 8px 0;
        padding-left: 11px;
    }}

    /* =========================================================================
       INPUTS & COMBOBOXES
       ========================================================================= */
    QLineEdit {{
        background: {c['panel_hi']};
        color: {c['text_bright']};
        border: 1px solid {c['line']};
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 13px;
        selection-background-color: {c['accent']};
    }}

    QLineEdit:hover {{
        border: 1px solid {c['subtext']};
    }}

    QLineEdit:focus {{
        border: 1.5px solid {c['accent']};
        background: {c['panel']};
    }}

    QComboBox {{
        background: {c['panel_hi']};
        color: {c['text_bright']};
        border: 1px solid {c['line']};
        border-radius: 8px;
        padding: 7px 12px;
        font-size: 12px;
        font-weight: 500;
        min-width: 130px;
    }}

    QComboBox:hover {{
        border: 1px solid {c['accent']};
    }}

    QComboBox:focus {{
        border: 1.5px solid {c['accent']};
    }}

    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 24px;
        border-left: 1px solid {c['line']};
    }}

    QComboBox QAbstractItemView {{
        background: {c['panel']};
        color: {c['text']};
        border: 1px solid {c['line']};
        border-radius: 8px;
        selection-background-color: {c['accent']};
        selection-color: #FFFFFF;
        padding: 4px;
    }}

    /* =========================================================================
       SLIDERS
       ========================================================================= */
    QSlider::groove:horizontal {{
        height: 6px;
        background: {c['raised']};
        border-radius: 3px;
    }}

    QSlider::sub-page:horizontal {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c['accent']}, stop:1 {c['accent_hi']});
        border-radius: 3px;
    }}

    QSlider::handle:horizontal {{
        background: {c['panel']};
        border: 2px solid {c['accent']};
        width: 16px;
        height: 16px;
        margin: -5px 0;
        border-radius: 8px;
    }}

    QSlider::handle:horizontal:hover {{
        background: {c['accent']};
        border: 2px solid #FFFFFF;
        width: 18px;
        height: 18px;
        margin: -6px 0;
        border-radius: 9px;
    }}

    /* =========================================================================
       PROGRESS BARS
       ========================================================================= */
    QProgressBar {{
        background: {c['raised']};
        border: none;
        border-radius: 4px;
        height: 6px;
        text-align: center;
    }}

    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c['accent']}, stop:1 {c['info']});
        border-radius: 4px;
    }}

    /* =========================================================================
       CHECKBOXES
       ========================================================================= */
    QCheckBox {{
        color: {c['text_bright']};
        spacing: 9px;
        font-size: 13px;
    }}

    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 1px solid {c['line']};
        border-radius: 5px;
        background: {c['panel_hi']};
    }}

    QCheckBox::indicator:hover {{
        border: 1.5px solid {c['accent']};
    }}

    QCheckBox::indicator:checked {{
        background: {c['accent']};
        border: 1.5px solid {c['accent_hi']};
    }}

    /* =========================================================================
       SLEEK MODERN SCROLLBARS
       ========================================================================= */
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background: {c['raised']};
        min-height: 24px;
        border-radius: 4px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {c['accent']};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
        background: none;
    }}

    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}

    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
        margin: 0;
    }}

    QScrollBar::handle:horizontal {{
        background: {c['raised']};
        min-width: 24px;
        border-radius: 4px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background: {c['accent']};
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
        background: none;
    }}

    /* =========================================================================
       MODALS & DIALOGS
       ========================================================================= */
    QDialog {{
        background: {c['bg']};
    }}

    QMessageBox {{
        background: {c['panel']};
    }}

    QMessageBox QLabel {{
        color: {c['text']};
        font-size: 13px;
    }}

    QToolTip {{
        background: {c['panel_hi']};
        color: {c['text_bright']};
        border: 1px solid {c['line']};
        border-radius: 6px;
        padding: 5px 8px;
        font-size: 11px;
    }}
    """
