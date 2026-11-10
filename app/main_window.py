"""Pixora desktop application main window and workspace router."""
from __future__ import annotations

from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.animations import AnimatedStackedWidget
from app.best_shots_page import BestShotsPage
from app.categories_page import CategoriesPage
from app.dashboard import Dashboard
from app.duplicates_page import DuplicatesPage
from app.enhancer_page import EnhancerPage
from app.gallery_page import GalleryPage
from app.processed_page import ProcessedPage
from app.settings_page import SettingsPage
from app.theme import DARK, LIGHT, stylesheet
from core.logger import logger
from database.db_manager import DatabaseManager
from workers.scanning_worker import ScanningWorker

PAGE_DEFS = [
    ("Home", "🏠 Home"),
    ("My Gallery", "🖼️ My Gallery"),
    ("Smart Categories", "🏷️ Smart Categories"),
    ("Duplicate Finder", "👥 Duplicate Finder"),
    ("Similar Photos", "🪞 Similar Photos"),
    ("Best Shots", "⭐ Best Shots"),
    ("Image Enhancer", "✨ Image Enhancer"),
    ("Recently Processed", "🕒 Recently Processed"),
    ("Settings", "⚙️ Settings"),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dark = True
        self.nav_buttons = []
        self.database = DatabaseManager()
        self.worker: Optional[ScanningWorker] = None
        self.imported_current = 0

        self.setWindowTitle("Pixora — AI-Powered Smart Photo Studio")
        self.resize(1300, 840)
        self.setMinimumSize(1020, 680)

        central = QWidget()
        self.setCentralWidget(central)
        outer = QHBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Sidebar navigation
        sidebar = QFrame(objectName="sidebar")
        sidebar.setFixedWidth(245)
        nav = QVBoxLayout(sidebar)
        nav.setContentsMargins(14, 24, 14, 18)
        nav.setSpacing(4)

        # Brand header
        brand_row = QHBoxLayout()
        brand_row.setSpacing(8)
        brand_logo = QLabel("✦")
        brand_logo.setStyleSheet("font-size: 20px; color: #7C6CFF;")
        brand = QLabel("PIXORA", objectName="brand")
        brand_row.addWidget(brand_logo)
        brand_row.addWidget(brand)
        brand_row.addStretch()
        nav.addLayout(brand_row)

        sub_brand = QLabel("CREATIVE PHOTO STUDIO", objectName="section")
        sub_brand.setStyleSheet("margin-left: 28px; margin-top: -2px;")
        nav.addWidget(sub_brand)
        nav.addSpacing(22)

        # Section label
        nav.addWidget(QLabel("WORKSPACES", objectName="section"))
        nav.addSpacing(6)

        # Instantiate animated router & all workspace pages
        self.stack = AnimatedStackedWidget()
        self.dashboard = Dashboard(self.import_folder)
        self.gallery_page = GalleryPage(
            self.database,
            import_callback=self.import_folder,
            on_enhance_callback=self.open_in_enhancer,
        )
        self.categories_page = CategoriesPage(
            self.database,
            on_enhance_callback=self.open_in_enhancer,
        )
        self.duplicate_page = DuplicatesPage(
            self.database,
            mode="exact",
            on_enhance_callback=self.open_in_enhancer,
        )
        self.similar_page = DuplicatesPage(
            self.database,
            mode="similar",
            on_enhance_callback=self.open_in_enhancer,
        )
        self.best_shots_page = BestShotsPage(
            self.database,
            on_enhance_callback=self.open_in_enhancer,
        )
        self.enhancer_page = EnhancerPage(self.database)
        self.processed_page = ProcessedPage(self.database)
        self.settings_page = SettingsPage(self.apply_theme, self.database)
        self.settings_page.library_cleared.connect(self.on_library_cleared)

        self.pages_map = {
            "Home": self.dashboard,
            "My Gallery": self.gallery_page,
            "Smart Categories": self.categories_page,
            "Duplicate Finder": self.duplicate_page,
            "Similar Photos": self.similar_page,
            "Best Shots": self.best_shots_page,
            "Image Enhancer": self.enhancer_page,
            "Recently Processed": self.processed_page,
            "Settings": self.settings_page,
        }

        for index, (key, display_label) in enumerate(PAGE_DEFS):
            button = QPushButton(display_label, objectName="navButton")
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda checked=False, i=index: self.switch_page(i))
            nav.addWidget(button)
            self.nav_buttons.append(button)

            self.stack.addWidget(self.pages_map[key])

            if key == "Recently Processed":
                nav.addSpacing(14)
                nav.addWidget(QLabel("PREFERENCES", objectName="section"))
                nav.addSpacing(4)

        nav.addStretch()

        # Engine status card at sidebar footer
        status_box = QFrame(objectName="glassPanel")
        status_box.setStyleSheet("padding: 8px 10px; background: rgba(124, 108, 255, 0.08); border-radius: 8px;")
        s_layout = QVBoxLayout(status_box)
        s_layout.setContentsMargins(8, 8, 8, 8)
        s_layout.setSpacing(3)
        
        status_top = QHBoxLayout()
        dot = QLabel("●")
        dot.setStyleSheet("color: #10B981; font-size: 10px;")
        status_title = QLabel("LOCAL ENGINE", styleSheet="font-size: 11px; font-weight: 700; color: #10B981; letter-spacing: 0.8px;")
        status_top.addWidget(dot)
        status_top.addWidget(status_title)
        status_top.addStretch()
        s_layout.addLayout(status_top)
        
        status_sub = QLabel("100% Private • Offline CV", styleSheet="font-size: 11px; color: #7C8497;")
        s_layout.addWidget(status_sub)
        nav.addWidget(status_box)

        outer.addWidget(sidebar)
        outer.addWidget(self.stack, 1)

        # Load persisted settings and update dashboard
        self.dashboard.set_existing_count(self.database.count_images())
        saved_theme = self.database.get_setting("theme", "dark")
        self.apply_theme(saved_theme == "light")
        self.switch_page(0)
        logger.info("Pixora desktop studio initialized successfully with motion design")

    def switch_page(self, index: int):
        self.stack.slide_to_index(index)
        for i, button in enumerate(self.nav_buttons):
            button.setObjectName("navActive" if i == index else "navButton")
            button.style().unpolish(button)
            button.style().polish(button)

        # Refresh page state on navigation
        active_page = self.stack.currentWidget()
        if isinstance(active_page, GalleryPage):
            active_page.reload_gallery()
        elif isinstance(active_page, CategoriesPage):
            active_page.refresh_badges()
            active_page.render_filtered_photos()
        elif isinstance(active_page, DuplicatesPage):
            active_page.reload_groups()
        elif isinstance(active_page, BestShotsPage):
            active_page.reload_photos()
        elif isinstance(active_page, ProcessedPage):
            active_page.reload_list()

    def open_in_enhancer(self, image_path: str):
        """Seamless state handoff: opens photo in Image Enhancer Studio from any page."""
        idx = [k for k, _ in PAGE_DEFS].index("Image Enhancer")
        self.switch_page(idx)
        self.enhancer_page.load_image(image_path)

    def on_library_cleared(self):
        self.dashboard.set_existing_count(0)
        self.gallery_page.reload_gallery()
        self.categories_page.refresh_badges()
        self.categories_page.render_filtered_photos()

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
        total_count = self.database.count_images()
        self.dashboard.set_import_summary(total_count, result, Path(folder).name)
        self.gallery_page.reload_gallery()
        logger.info(f"Import finished from {folder}: {result['imported']} imported")

    def scan_failed(self, error: str):
        logger.error(f"Scan failed: {error}")
        QMessageBox.critical(self, "Could not import folder", error)

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(1500)
        for page in (
            self.gallery_page,
            self.categories_page,
            self.duplicate_page,
            self.similar_page,
            self.best_shots_page,
            self.enhancer_page,
        ):
            w = getattr(page, "worker", None) or getattr(page, "thumb_worker", None)
            if w and w.isRunning():
                w.cancel()
                w.wait(1000)
        self.database.close()
        event.accept()
