"""Comprehensive settings page for Pixora photo studio."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.logger import logger
from database.db_manager import DatabaseManager


class SettingsPage(QWidget):
    library_cleared = Signal()

    def __init__(
        self,
        toggle_theme: Callable[[bool], None],
        database: DatabaseManager,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.toggle_theme = toggle_theme
        self.database = database

        root = QVBoxLayout(self)
        root.setContentsMargins(36, 30, 36, 30)
        root.setSpacing(20)

        # Header
        root.addWidget(QLabel("Settings & Preferences", objectName="pageTitle"))
        root.addWidget(QLabel("Configure appearance, storage paths, quality metrics, and library data.", objectName="muted"))

        # 1. Appearance Card
        c1 = QFrame(objectName="card")
        l1 = QVBoxLayout(c1)
        l1.setContentsMargins(20, 18, 20, 18)
        l1.setSpacing(10)
        l1.addWidget(QLabel("Appearance", styleSheet="font-size: 16px; font-weight: 700;"))

        self.theme_check = QCheckBox("Use Light Mode")
        is_light = self.database.get_setting("theme", "dark") == "light"
        self.theme_check.setChecked(is_light)
        self.theme_check.toggled.connect(self._handle_theme_toggle)
        l1.addWidget(self.theme_check)
        root.addWidget(c1)

        # 2. Storage & Export Directory Card
        c2 = QFrame(objectName="card")
        l2 = QVBoxLayout(c2)
        l2.setContentsMargins(20, 18, 20, 18)
        l2.setSpacing(10)
        l2.addWidget(QLabel("Processed Output Directory", styleSheet="font-size: 16px; font-weight: 700;"))
        l2.addWidget(
            QLabel("Where enhanced copies and exported images are saved. Your original source photos are never modified.", objectName="muted")
        )

        dir_row = QHBoxLayout()
        self.dir_input = QLineEdit()
        current_dir = self.database.get_setting("processed_dir", str(Path("processed").resolve()))
        self.dir_input.setText(current_dir)
        self.dir_input.setReadOnly(True)
        self.dir_input.setStyleSheet("padding: 8px 12px; border-radius: 8px; border: 1px solid #292E3B;")
        dir_row.addWidget(self.dir_input, stretch=1)

        btn_browse = QPushButton("Change Folder…", objectName="secondary")
        btn_browse.setCursor(Qt.PointingHandCursor)
        btn_browse.clicked.connect(self._choose_output_dir)
        dir_row.addWidget(btn_browse)

        btn_default = QPushButton("Reset Default", objectName="secondary")
        btn_default.setCursor(Qt.PointingHandCursor)
        btn_default.clicked.connect(self._reset_output_dir)
        dir_row.addWidget(btn_default)

        l2.addLayout(dir_row)
        root.addWidget(c2)

        # 3. Quality & Blur Thresholds Card
        c3 = QFrame(objectName="card")
        l3 = QVBoxLayout(c3)
        l3.setContentsMargins(20, 18, 20, 18)
        l3.setSpacing(12)
        l3.addWidget(QLabel("Quality & Blur Sensitivity", styleSheet="font-size: 16px; font-weight: 700;"))
        l3.addWidget(
            QLabel("Tune deterministic computer vision thresholds for sharpness and 'Needs Review' blur detection.", objectName="muted")
        )

        # Blur threshold slider
        blur_val = float(self.database.get_setting("blur_threshold", "130.0"))
        blur_row = QHBoxLayout()
        blur_row.addWidget(QLabel("Blur Cutoff (Laplacian Variance):", styleSheet="font-weight: 600;"))
        self.blur_lbl = QLabel(f"{int(blur_val)}", objectName="pill")
        blur_row.addStretch()
        blur_row.addWidget(self.blur_lbl)
        l3.addLayout(blur_row)

        self.blur_slider = QSlider(Qt.Horizontal)
        self.blur_slider.setRange(40, 400)
        self.blur_slider.setValue(int(blur_val))
        self.blur_slider.valueChanged.connect(self._on_blur_changed)
        l3.addWidget(self.blur_slider)

        l3.addWidget(
            QLabel("Images with edge variance below this cutoff are tagged as 'Blurry / Soft' in Best Shots.", objectName="muted")
        )

        root.addWidget(c3)

        # 4. Privacy & Maintenance Card
        c4 = QFrame(objectName="card")
        l4 = QVBoxLayout(c4)
        l4.setContentsMargins(20, 18, 20, 18)
        l4.setSpacing(12)
        l4.addWidget(QLabel("Privacy & Library Maintenance", styleSheet="font-size: 16px; font-weight: 700;"))

        local_privacy = QCheckBox("Local-Only Privacy: Zero cloud uploads, zero telemetry")
        local_privacy.setChecked(True)
        local_privacy.setEnabled(False)
        l4.addWidget(local_privacy)

        btn_row = QHBoxLayout()
        btn_logs = QPushButton("View Application Logs", objectName="secondary")
        btn_logs.setCursor(Qt.PointingHandCursor)
        btn_logs.clicked.connect(self._view_logs)
        btn_row.addWidget(btn_logs)

        btn_clear = QPushButton("Clear Local Index…", objectName="secondary")
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.setStyleSheet("color: #E27D60;")
        btn_clear.clicked.connect(self._clear_index)
        btn_row.addWidget(btn_clear)
        btn_row.addStretch()

        l4.addLayout(btn_row)
        root.addWidget(c4)

        root.addStretch()

    def _handle_theme_toggle(self, checked: bool):
        self.database.set_setting("theme", "light" if checked else "dark")
        self.toggle_theme(checked)

    def _choose_output_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Processed Output Directory", self.dir_input.text())
        if folder:
            self.dir_input.setText(folder)
            self.database.set_setting("processed_dir", folder)

    def _reset_output_dir(self):
        default_dir = str(Path("processed").resolve())
        self.dir_input.setText(default_dir)
        self.database.set_setting("processed_dir", default_dir)

    def _on_blur_changed(self, value: int):
        self.blur_lbl.setText(str(value))
        self.database.set_setting("blur_threshold", str(value))

    def _view_logs(self):
        app_data = Path(os.environ.get("PIXORA_DATA_DIR", Path.home() / ".pixora"))
        log_file = app_data / "pixora.log"
        if not log_file.is_file():
            QMessageBox.information(self, "No Logs Yet", "Application log file has not been created yet.")
            return

        if sys.platform == "win32":
            os.startfile(str(log_file))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(log_file)])
        else:
            subprocess.run(["xdg-open", str(log_file)])

    def _clear_index(self):
        reply = QMessageBox.warning(
            self,
            "Clear Local Image Index",
            "Are you sure you want to clear Pixora's local library index?\n\n"
            "• Your original photo files on disk will NOT be touched or deleted.\n"
            "• Pixora will simply reset its local SQLite index.\n\n"
            "Do you want to proceed?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.database.clear_library(delete_processed=False)
            QMessageBox.information(self, "Index Cleared", "The local index has been successfully reset.")
            self.library_cleared.emit()

