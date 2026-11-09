from PySide6.QtGui import QColor, QPalette

DARK = {
    "bg": "#101114", "surface": "#191b20", "surface2": "#22252c",
    "text": "#F4F4F6", "muted": "#999CA8", "line": "#30333b",
    "accent": "#9A8CFF", "accent_hover": "#B2A7FF", "success": "#55D49B",
}
LIGHT = {
    "bg": "#F7F7FA", "surface": "#FFFFFF", "surface2": "#EFEFF4",
    "text": "#17171A", "muted": "#6D6E78", "line": "#DEDDE5",
    "accent": "#6557D8", "accent_hover": "#5145B8", "success": "#168B5A",
}


def stylesheet(colors: dict) -> str:
    return f"""
    * {{ font-family: 'Segoe UI'; }}
    QMainWindow, QWidget {{ background: {colors['bg']}; color: {colors['text']}; }}
    QFrame#sidebar {{ background: {colors['surface']}; border-right: 1px solid {colors['line']}; }}
    QLabel#brand {{ font-size: 22px; font-weight: 700; }}
    QLabel#eyebrow {{ color: {colors['muted']}; font-size: 12px; font-weight: 600; letter-spacing: 1px; }}
    QLabel#pageTitle {{ font-size: 30px; font-weight: 700; }}
    QLabel#muted {{ color: {colors['muted']}; font-size: 14px; }}
    QPushButton {{ border: 0; border-radius: 9px; padding: 9px 12px; font-size: 14px; color: {colors['text']}; background: transparent; text-align: left; }}
    QPushButton:hover {{ background: {colors['surface2']}; }}
    QPushButton#navActive {{ background: {colors['accent']}; color: white; font-weight: 600; }}
    QPushButton#primary {{ background: {colors['accent']}; color: white; font-weight: 600; padding: 10px 16px; }}
    QPushButton#primary:hover {{ background: {colors['accent_hover']}; }}
    QFrame#card {{ background: {colors['surface']}; border: 1px solid {colors['line']}; border-radius: 14px; }}
    QLineEdit, QComboBox {{ background: {colors['surface']}; border: 1px solid {colors['line']}; border-radius: 9px; padding: 9px 12px; color: {colors['text']}; }}
    QLineEdit:focus, QComboBox:focus {{ border: 1px solid {colors['accent']}; }}
    QProgressBar {{ border: 0; border-radius: 4px; background: {colors['surface2']}; height: 7px; }}
    QProgressBar::chunk {{ background: {colors['accent']}; border-radius: 4px; }}
    QCheckBox {{ color: {colors['text']}; spacing: 9px; }}
    QCheckBox::indicator {{ width: 17px; height: 17px; border: 1px solid {colors['line']}; border-radius: 5px; background: {colors['surface']}; }}
    QCheckBox::indicator:checked {{ background: {colors['accent']}; border-color: {colors['accent']}; }}
    """
