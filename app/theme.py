"""Pixora's semantic native-desktop design tokens."""

DARK = {"bg":"#0B0C10","panel":"#12141B","panel_hi":"#191C25","raised":"#202431","text":"#F7F8FC","subtext":"#B2B8C8","muted":"#7C8497","line":"#292E3B","accent":"#7C6CFF","accent_hi":"#9387FF"}
LIGHT = {"bg":"#F5F6FA","panel":"#FFFFFF","panel_hi":"#F9FAFC","raised":"#EEF0F6","text":"#171923","subtext":"#50586B","muted":"#737C90","line":"#DDE1EA","accent":"#5E50D6","accent_hi":"#5043C0"}

def stylesheet(c: dict) -> str:
    return f"""
    * {{ font-family: 'Segoe UI'; font-size: 14px; }} QMainWindow, QWidget {{ background:{c['bg']}; color:{c['text']}; }}
    QFrame#sidebar {{ background:{c['panel']}; border-right:1px solid {c['line']}; }} QFrame#card,QFrame#featureCard {{ background:{c['panel']}; border:1px solid {c['line']}; border-radius:16px; }} QFrame#featureCard {{ background:{c['panel_hi']}; }}
    QLabel#brand {{ font-size:23px; font-weight:700; }} QLabel#section {{ color:{c['muted']}; font-size:11px; font-weight:700; letter-spacing:1.2px; }} QLabel#pageTitle {{ font-size:27px; font-weight:700; }} QLabel#pageSub,QLabel#muted {{ color:{c['subtext']}; font-size:14px; }} QLabel#metric {{ font-size:31px; font-weight:700; color:{c['text']}; }} QLabel#metricLabel {{ color:{c['muted']}; font-size:12px; font-weight:600; }} QLabel#pill {{ background:{c['raised']}; color:{c['subtext']}; border-radius:10px; padding:5px 9px; font-size:12px; }}
    QPushButton {{ color:{c['subtext']}; background:transparent; border:0; border-radius:9px; padding:10px 12px; text-align:left; min-height:20px; }} QPushButton:hover {{ background:{c['raised']}; color:{c['text']}; }} QPushButton:focus {{ border:1px solid {c['accent_hi']}; }} QPushButton#navActive {{ background:{c['raised']}; color:{c['text']}; font-weight:700; border-left:3px solid {c['accent_hi']}; padding-left:9px; }} QPushButton#primary {{ background:{c['accent']}; color:white; font-weight:700; padding:10px 16px; }} QPushButton#primary:hover {{ background:{c['accent_hi']}; }} QPushButton#secondary {{ background:{c['raised']}; color:{c['text']}; font-weight:600; }}
    QProgressBar {{ border:0; border-radius:4px; background:{c['raised']}; height:8px; }} QProgressBar::chunk {{ background:{c['accent']}; border-radius:4px; }} QCheckBox {{ color:{c['text']}; spacing:10px; padding:5px 0; }} QCheckBox::indicator {{ width:18px; height:18px; border:1px solid {c['line']}; border-radius:5px; background:{c['panel']}; }} QCheckBox::indicator:checked {{ background:{c['accent']}; border-color:{c['accent']}; }}
    """
