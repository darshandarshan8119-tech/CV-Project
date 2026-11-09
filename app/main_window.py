from pathlib import Path
from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton, QStackedWidget, QVBoxLayout, QWidget, QCheckBox
from app.dashboard import Dashboard
from app.theme import DARK, LIGHT, stylesheet

PAGES = ["Home", "My Gallery", "Smart Categories", "Duplicate Finder", "Similar Photos", "Best Shots", "Image Enhancer", "Recently Processed", "Settings"]

class PlaceholderPage(QWidget):
    def __init__(self, name):
        super().__init__(); layout = QVBoxLayout(self); layout.setContentsMargins(36, 30, 36, 30); layout.setAlignment(Qt.AlignCenter)
        title = QLabel(name, objectName="pageTitle"); title.setAlignment(Qt.AlignCenter)
        message = QLabel("This workspace will become available as Pixora’s next capability is built.\nPhase 1 is focused on the app foundation and interface.", objectName="muted"); message.setAlignment(Qt.AlignCenter)
        layout.addWidget(title); layout.addWidget(message)

class SettingsPage(QWidget):
    def __init__(self, toggle_theme):
        super().__init__(); root = QVBoxLayout(self); root.setContentsMargins(36, 30, 36, 30); root.setSpacing(20)
        root.addWidget(QLabel("Settings", objectName="pageTitle")); root.addWidget(QLabel("Choose how Pixora feels and protects your library.", objectName="muted"))
        panel = QFrame(objectName="card"); layout = QVBoxLayout(panel); layout.setContentsMargins(20, 18, 20, 18); layout.setSpacing(14)
        layout.addWidget(QLabel("Appearance", styleSheet="font-size: 17px; font-weight: 600;")); light = QCheckBox("Use light appearance"); light.toggled.connect(toggle_theme); layout.addWidget(light)
        layout.addSpacing(8); layout.addWidget(QLabel("Privacy", styleSheet="font-size: 17px; font-weight: 600;")); local = QCheckBox("Keep all analysis and processing local"); local.setChecked(True); local.setEnabled(False); layout.addWidget(local)
        root.addWidget(panel); root.addStretch()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.dark = True; self.nav_buttons = []
        self.setWindowTitle("Pixora — AI-Powered Smart Photo Studio"); self.resize(1240, 780); self.setMinimumSize(960, 620)
        central = QWidget(); self.setCentralWidget(central); outer = QHBoxLayout(central); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        sidebar = QFrame(objectName="sidebar"); sidebar.setFixedWidth(238); nav = QVBoxLayout(sidebar); nav.setContentsMargins(14, 22, 14, 16); nav.setSpacing(5)
        brand = QLabel("◉  Pixora", objectName="brand"); nav.addWidget(brand); nav.addWidget(QLabel("SMART PHOTO STUDIO", objectName="eyebrow")); nav.addSpacing(22)
        self.stack = QStackedWidget(); self.stack.addWidget(Dashboard(self.import_folder))
        for index, page in enumerate(PAGES):
            button = QPushButton(page); button.setCursor(Qt.PointingHandCursor); button.clicked.connect(lambda checked=False, i=index: self.switch_page(i)); nav.addWidget(button); self.nav_buttons.append(button)
            if index > 0: self.stack.addWidget(SettingsPage(self.apply_theme) if page == "Settings" else PlaceholderPage(page))
            if page == "Image Enhancer": nav.addSpacing(10)
        nav.addStretch(); status = QLabel("●  Local-only processing", objectName="muted"); status.setStyleSheet("color: #55D49B;"); nav.addWidget(status)
        outer.addWidget(sidebar); outer.addWidget(self.stack, 1); self.switch_page(0); self.apply_theme(False)

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons): button.setObjectName("navActive" if i == index else "")
        self.style().unpolish(self); self.style().polish(self)

    def apply_theme(self, light: bool):
        self.dark = not light; self.setStyleSheet(stylesheet(DARK if self.dark else LIGHT))

    def import_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Choose your photo folder", str(Path.home()))
        if path:
            QMessageBox.information(self, "Folder selected", f"Pixora will import photos from:\n{path}\n\nFolder scanning arrives in Phase 2.")
