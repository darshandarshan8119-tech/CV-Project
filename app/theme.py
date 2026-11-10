"""Pixora's premium creative-software theme tokens and comprehensive styling.

Features:
- Deep Charcoal / Obsidian dark mode with vibrant electric-violet & cyan accents.
- Modern Glassmorphism panel and card definitions with soft translucent borders.
- Sleek modern scrollbars, sliders, inputs, dropdowns, and buttons.
- Light mode support (clean Studio Titanium palette).
"""
from __future__ import annotations

DARK = {
    # Backgrounds & canvas
    "bg": "#090A0F",
    "bg_subtle": "#0F1118",
    "panel": "#141722",
    "panel_hi": "#1B2030",
    "raised": "#232A3E",
    "raised_hover": "#2B334B",
    
    # Glassmorphism tokens
    "glass_bg": "rgba(20, 23, 34, 0.78)",
    "glass_border": "rgba(255, 255, 255, 0.08)",
    "glass_border_hi": "rgba(124, 108, 255, 0.35)",
    
    # Text
    "text": "#F3F5FA",
    "text_bright": "#FFFFFF",
    "subtext": "#9FA9C0",
    "muted": "#69738A",
    "line": "#262D40",
    "line_subtle": "#1B2030",
    
    # Accents & Glows
    "accent": "#7C6CFF",
    "accent_hi": "#9487FF",
    "accent_deep": "#5B4AE0",
    "accent_glow": "rgba(124, 108, 255, 0.28)",
    "accent_light": "rgba(124, 108, 255, 0.12)",
    
    # Status / Functional Colors
    "success": "#10B981",
    "success_glow": "rgba(16, 185, 129, 0.25)",
    "success_bg": "rgba(16, 185, 129, 0.12)",
    "warning": "#F59E0B",
    "warning_glow": "rgba(245, 158, 11, 0.25)",
    "danger": "#F43F5E",
    "danger_glow": "rgba(244, 63, 94, 0.25)",
    "info": "#06B6D4",
    
    # Shadows
    "shadow_sm": "rgba(0, 0, 0, 0.35)",
    "shadow_lg": "rgba(0, 0, 0, 0.55)",
}

LIGHT = {
    "bg": "#F5F7FB",
    "bg_subtle": "#ECEFF5",
    "panel": "#FFFFFF",
    "panel_hi": "#F8FAFC",
    "raised": "#EDF2F7",
    "raised_hover": "#E2E8F0",
    
    "glass_bg": "rgba(255, 255, 255, 0.88)",
    "glass_border": "rgba(0, 0, 0, 0.08)",
    "glass_border_hi": "rgba(94, 80, 214, 0.3)",
    
    "text": "#0F172A",
    "text_bright": "#020617",
    "subtext": "#475569",
    "muted": "#94A3B8",
    "line": "#E2E8F0",
    "line_subtle": "#EEF2F6",
    
    "accent": "#6355FF",
    "accent_hi": "#5143EE",
    "accent_deep": "#4031D4",
    "accent_glow": "rgba(99, 85, 255, 0.22)",
    "accent_light": "rgba(99, 85, 255, 0.08)",
    
    "success": "#059669",
    "success_glow": "rgba(5, 150, 105, 0.2)",
    "success_bg": "rgba(5, 150, 105, 0.08)",
    "warning": "#D97706",
    "warning_glow": "rgba(217, 119, 6, 0.2)",
    "danger": "#E11D48",
    "danger_glow": "rgba(225, 29, 72, 0.2)",
    "info": "#0891B2",
    
    "shadow_sm": "rgba(0, 0, 0, 0.06)",
    "shadow_lg": "rgba(0, 0, 0, 0.12)",
}


def stylesheet(c: dict) -> str:
    """Generate high-fidelity desktop stylesheet with modern creative-software aesthetics."""
    return f"""
    * {{
        font-family: 'Segoe UI', -apple-system, 'SF Pro Display', BlinkMacSystemFont, Roboto, sans-serif;
        font-size: 13px;
        color: {c['text']};
        outline: none;
    }}

    QMainWindow, QWidget {{
        background: {c['bg']};
        color: {c['text']};
    }}

    /* =========================================================================
       SIDEBAR & NAVIGATION
       ========================================================================= */
    QFrame#sidebar {{
        background: {c['panel']};
        border-right: 1px solid {c['line']};
    }}

    QLabel#brand {{
        font-size: 20px;
        font-weight: 800;
        letter-spacing: 2px;
        color: {c['text_bright']};
    }}

    QLabel#brandAccent {{
        color: {c['accent']};
    }}

    QLabel#section {{
        color: {c['muted']};
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }}

    /* =========================================================================
       CARDS & PANELS (Glassmorphism & Neumorphic depths)
       ========================================================================= */
    QFrame#card {{
        background: {c['panel']};
        border: 1px solid {c['line']};
        border-radius: 12px;
    }}
    QFrame#card:hover {{
        border: 1px solid {c['line']};
    }}

    QFrame#featureCard {{
        background: {c['panel_hi']};
        border: 1px solid {c['glass_border_hi']};
        border-radius: 14px;
    }}

    QFrame#glassPanel {{
        background: {c['glass_bg']};
        border: 1px solid {c['glass_border']};
        border-radius: 14px;
    }}

    /* =========================================================================
       TYPOGRAPHY HIERARCHY
       ========================================================================= */
    QLabel#pageTitle {{
        font-size: 24px;
        font-weight: 700;
        color: {c['text_bright']};
        letter-spacing: -0.3px;
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

    QLabel#pill {{
        background: {c['raised']};
        color: {c['subtext']};
        border: 1px solid {c['line']};
        border-radius: 12px;
        padding: 4px 10px;
        font-size: 11px;
        font-weight: 600;
    }}

    QLabel#pillActive {{
        background: {c['accent_light']};
        color: {c['accent_hi']};
        border: 1px solid {c['glass_border_hi']};
        border-radius: 12px;
        padding: 4px 10px;
        font-size: 11px;
        font-weight: 700;
    }}

    QLabel#pillSuccess {{
        background: {c['success_bg']};
        color: {c['success']};
        border: 1px solid {c['success_glow']};
        border-radius: 12px;
        padding: 4px 10px;
        font-size: 11px;
        font-weight: 700;
    }}

    /* =========================================================================
       BUTTONS
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
        border: 1px solid {c['subtext']};
        color: {c['text_bright']};
    }}

    QPushButton:pressed {{
        background: {c['panel_hi']};
        border: 1px solid {c['accent']};
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
        border: 1px solid #FFFFFF;
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
        border: 1px solid {c['subtext']};
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

    QLineEdit:focus {{
        border: 1px solid {c['accent']};
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
        border: 1px solid {c['subtext']};
    }}

    QComboBox:focus {{
        border: 1px solid {c['accent']};
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
        background: {c['text_bright']};
        border: 2px solid {c['accent']};
        width: 16px;
        height: 16px;
        margin: -5px 0;
        border-radius: 8px;
    }}

    QSlider::handle:horizontal:hover {{
        background: {c['accent_hi']};
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
        color: {c['text']};
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
        border: 1px solid {c['accent']};
    }}

    QCheckBox::indicator:checked {{
        background: {c['accent']};
        border: 1px solid {c['accent_hi']};
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
