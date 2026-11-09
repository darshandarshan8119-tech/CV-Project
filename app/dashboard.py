from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


def card(title: str, value: str, detail: str, accent: str = "") -> QFrame:
    box = QFrame(objectName="card")
    layout = QVBoxLayout(box); layout.setContentsMargins(18, 16, 18, 16); layout.setSpacing(7)
    label = QLabel(title.upper(), objectName="eyebrow")
    value_label = QLabel(value); value_label.setStyleSheet(f"font-size: 27px; font-weight: 700; color: {accent or 'inherit'};")
    detail_label = QLabel(detail, objectName="muted")
    layout.addWidget(label); layout.addWidget(value_label); layout.addWidget(detail_label)
    return box


class Dashboard(QWidget):
    def __init__(self, import_action):
        super().__init__()
        root = QVBoxLayout(self); root.setContentsMargins(36, 30, 36, 30); root.setSpacing(24)
        header = QHBoxLayout()
        title_area = QVBoxLayout(); title_area.setSpacing(3)
        title_area.addWidget(QLabel("Good afternoon", objectName="pageTitle"))
        title_area.addWidget(QLabel("Your private photo library is ready when you are.", objectName="muted"))
        import_button = QPushButton("Import folder", objectName="primary"); import_button.clicked.connect(import_action)
        header.addLayout(title_area); header.addStretch(); header.addWidget(import_button)
        root.addLayout(header)
        stats = QGridLayout(); stats.setHorizontalSpacing(14); stats.setVerticalSpacing(14)
        data = [("Photos", "0", "Start by importing a folder"), ("Duplicates", "—", "Scan your library to detect"), ("Categories", "0", "Organize memories automatically"), ("Needs review", "—", "Blur and quality checks")]
        for index, entry in enumerate(data): stats.addWidget(card(*entry), 0, index)
        root.addLayout(stats)
        welcome = QFrame(objectName="card"); welcome.setMinimumHeight(230)
        wl = QVBoxLayout(welcome); wl.setContentsMargins(28, 26, 28, 26); wl.setSpacing(10)
        badge = QLabel("PIXORA STARTER", objectName="eyebrow"); badge.setStyleSheet("color: #9A8CFF;")
        headline = QLabel("Bring your photo library\ninto focus."); headline.setStyleSheet("font-size: 29px; font-weight: 700;")
        copy = QLabel("Import a folder to explore your photos, uncover duplicates,\nand get thoughtful quality recommendations — all on your device.", objectName="muted")
        start = QPushButton("Choose a photo folder  →", objectName="primary"); start.setFixedWidth(202); start.clicked.connect(import_action)
        wl.addWidget(badge); wl.addWidget(headline); wl.addWidget(copy); wl.addStretch(); wl.addWidget(start)
        root.addWidget(welcome)
        lower = QHBoxLayout(); lower.setSpacing(14)
        activity = QFrame(objectName="card"); al = QVBoxLayout(activity); al.setContentsMargins(18, 18, 18, 18)
        al.addWidget(QLabel("Recent activity", styleSheet="font-size: 16px; font-weight: 600;")); al.addStretch(); empty = QLabel("No activity yet\nYour processed photos will appear here.", objectName="muted"); empty.setAlignment(Qt.AlignCenter); al.addWidget(empty); al.addStretch()
        privacy = QFrame(objectName="card"); pl = QVBoxLayout(privacy); pl.setContentsMargins(18, 18, 18, 18)
        pl.addWidget(QLabel("Private by design", styleSheet="font-size: 16px; font-weight: 600;")); pl.addWidget(QLabel("Pixora works locally. Your photographs stay on your computer and originals are never overwritten.", objectName="muted")); pl.addStretch()
        lower.addWidget(activity, 3); lower.addWidget(privacy, 2); root.addLayout(lower, 1)
