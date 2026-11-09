from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.categories_page import CategoriesPage
from app.dashboard import Dashboard
from app.duplicates_page import DuplicatesPage
from app.gallery_page import GalleryPage
from app.theme import DARK, LIGHT, stylesheet
from database.db_manager import DatabaseManager
from workers.scanning_worker import ScanningWorker

PAGES = [
    "Home",
    "My Gallery",
    "Smart Categories",
    "Duplicate Finder",
    "Similar Photos",
    "Best Shots",
    "Image Enhancer",
    "Recently Processed",
    "Settings",
]


class PlaceholderPage(QWidget):
    def __init__(self, name: str):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setAlignment(Qt.AlignCenter)
        title = QLabel(name, objectName="pageTitle")
        title.setAlignment(Qt.AlignCenter)
        message = QLabel(
            "This workspace will become available in a future phase.\nPhases 1–5 are currently active.",
            objectName="muted",
        )
        message.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(message)


class SettingsPage(QWidget):
    def __init__(self, toggle_theme):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 30, 36, 30)
        root.setSpacing(20)
        root.addWidget(QLabel("Settings", objectName="pageTitle"))
        root.addWidget(QLabel("Choose how Pixora feels and protects your library.", objectName="muted"))

        panel = QFrame(objectName="card")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        layout.addWidget(QLabel("Appearance", styleSheet="font-size: 17px; font-weight: 600;"))
        light = QCheckBox("Use light appearance")
        light.toggled.connect(toggle_theme)
        layout.addWidget(light)

        layout.addSpacing(8)
        layout.addWidget(QLabel("Privacy", styleSheet="font-size: 17px; font-weight: 600;"))
        local = QCheckBox("Keep all analysis and processing local")
        local.setChecked(True)
        local.setEnabled(False)
        layout.addWidget(local)

        root.addWidget(panel)
        root.addStretch()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dark = True
        self.nav_buttons = []
        self.database = DatabaseManager()
        self.worker = None
        self.imported_current = 0

        self.setWindowTitle("Pixora — AI-Powered Smart Photo Studio")
        self.resize(1240, 780)
        self.setMinimumSize(960, 620)

        central = QWidget()
        self.setCentralWidget(central)
        outer = QHBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        sidebar = QFrame(objectName="sidebar")
        sidebar.setFixedWidth(238)
        nav = QVBoxLayout(sidebar)
        nav.setContentsMargins(14, 22, 14, 16)
        nav.setSpacing(5)

        brand = QLabel("PIXORA", objectName="brand")
        nav.addWidget(brand)
        nav.addWidget(QLabel("SMART PHOTO STUDIO", objectName="section"))
        nav.addSpacing(22)

        self.stack = QStackedWidget()
        self.dashboard = Dashboard(self.import_folder)
        self.gallery_page = GalleryPage(self.database, self.import_folder)
        self.categories_page = CategoriesPage(self.database)
        self.duplicate_page = DuplicatesPage(self.database, mode="exact")
        self.similar_page = DuplicatesPage(self.database, mode="similar")

        self.pages_map = {
            "Home": self.dashboard,
            "My Gallery": self.gallery_page,
            "Smart Categories": self.categories_page,
            "Duplicate Finder": self.duplicate_page,
            "Similar Photos": self.similar_page,
        }

        for index, page in enumerate(PAGES):
            button = QPushButton(page)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda checked=False, i=index: self.switch_page(i))
            nav.addWidget(button)
            self.nav_buttons.append(button)

            if page in self.pages_map:
                self.stack.addWidget(self.pages_map[page])
            elif page == "Settings":
                self.stack.addWidget(SettingsPage(self.apply_theme))
            else:
                self.stack.addWidget(PlaceholderPage(page))

            if page == "Image Enhancer":
                nav.addSpacing(10)

        nav.addStretch()
        status = QLabel("LOCAL-ONLY PROCESSING", objectName="section")
        nav.addWidget(status)

        outer.addWidget(sidebar)
        outer.addWidget(self.stack, 1)

        self.dashboard.set_existing_count(self.database.count_images())
        self.switch_page(0)
        self.apply_theme(False)

    def switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons):
            button.setObjectName("navActive" if i == index else "")
        self.style().unpolish(self)
        self.style().polish(self)

        # Refresh page state on navigation
        active_page = self.stack.currentWidget()
        if isinstance(active_page, GalleryPage):
            active_page.reload_gallery()
        elif isinstance(active_page, CategoriesPage):
            active_page.refresh_badges()
            active_page.render_filtered_photos()
        elif isinstance(active_page, DuplicatesPage):
            active_page.reload_groups()

    def apply_theme(self, light: bool):
        self.dark = not light
        self.setStyleSheet(stylesheet(DARK if self.dark else LIGHT))

    def import_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Choose your photo folder", str(Path.home()))
        if path:
            if self.worker and self.worker.isRunning():
                QMessageBox.warning(self, "Import in progress", "Wait for the current folder import to finish.")
                return
            self.imported_current = 0
            self.worker = ScanningWorker(path)
            self.worker.started_scan.connect(self.dashboard.begin_scan)
            self.worker.progress.connect(self.dashboard.set_scan_progress)
            self.worker.image_found.connect(self.save_image)
            self.worker.completed.connect(lambda result: self.scan_finished(path, result))
            self.worker.failed.connect(self.scan_failed)
            self.worker.start()

    def save_image(self, record: dict):
        self.database.upsert_image(record)
        self.imported_current += 1

    def scan_finished(self, folder: str, result: dict):
        self.database.commit()
        self.dashboard.set_import_summary(self.database.count_images(), result, Path(folder).name)
        # Also reload gallery if user switches to it
        self.gallery_page.reload_gallery()

    def scan_failed(self, error: str):
        QMessageBox.critical(self, "Could not import folder", error)

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(1500)
        for page in (self.gallery_page, self.categories_page, self.duplicate_page, self.similar_page):
            w = getattr(page, "worker", None) or getattr(page, "thumb_worker", None)
            if w and w.isRunning():
                w.cancel()
                w.wait(1000)
        self.database.close()
        event.accept()
