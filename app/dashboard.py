from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget

def metric(label, value, note):
    box=QFrame(objectName="card"); l=QVBoxLayout(box); l.setContentsMargins(18,17,18,17); l.setSpacing(5)
    l.addWidget(QLabel(label.upper(),objectName="metricLabel")); number=QLabel(value,objectName="metric"); detail=QLabel(note,objectName="muted"); detail.setWordWrap(True); l.addWidget(number); l.addWidget(detail); return box,number,detail

class Dashboard(QWidget):
    def __init__(self, import_action):
        super().__init__(); root=QVBoxLayout(self); root.setContentsMargins(32,26,32,30); root.setSpacing(20)
        header=QHBoxLayout(); words=QVBoxLayout(); words.setSpacing(4); words.addWidget(QLabel("Your library",objectName="pageTitle")); words.addWidget(QLabel("Private, local photo intelligence — without changing your originals.",objectName="pageSub")); self.import_button=QPushButton("Import photo folder",objectName="primary"); self.import_button.clicked.connect(import_action); header.addLayout(words); header.addStretch(); header.addWidget(self.import_button); root.addLayout(header)
        self.metric_values={}; grid=QGridLayout(); grid.setSpacing(12)
        for col,(key,label,value,note) in enumerate([("photos","Library photos","0","No images imported yet"),("last","Last import","—","Choose a photo folder to begin"),("duplicates","Duplicate groups","—","Available after analysis"),("review","Needs review","—","Blur checks arrive next")]):
            box,num,detail=metric(label,value,note); grid.addWidget(box,0,col); self.metric_values[key]=(num,detail)
        root.addLayout(grid)
        panel=QFrame(objectName="featureCard"); pl=QVBoxLayout(panel); pl.setContentsMargins(23,20,23,20); pl.setSpacing(10); top=QHBoxLayout(); top.addWidget(QLabel("Import status",styleSheet="font-size:17px;font-weight:700;")); self.status=QLabel("READY",objectName="pill"); top.addStretch(); top.addWidget(self.status); pl.addLayout(top); self.status_detail=QLabel("Choose a folder. Pixora will index supported images in the background.",objectName="pageSub"); self.status_detail.setWordWrap(True); pl.addWidget(self.status_detail); self.progress=QProgressBar(); self.progress.setRange(0,1); self.progress.setValue(0); self.progress.setTextVisible(False); pl.addWidget(self.progress); root.addWidget(panel)
        lower=QHBoxLayout(); lower.setSpacing(12)
        for title,body in [("Start with a clean import","Pixora supports JPEG, PNG, WebP, BMP, TIFF and GIF. Unsupported or unreadable files are reported clearly."),("Your photos remain yours","All scanning runs on this computer. Pixora stores a local index and never automatically deletes or overwrites a file.")]:
            card=QFrame(objectName="card"); cl=QVBoxLayout(card); cl.setContentsMargins(21,19,21,19); cl.setSpacing(8); cl.addWidget(QLabel(title,styleSheet="font-size:17px;font-weight:700;")); copy=QLabel(body,objectName="pageSub"); copy.setWordWrap(True); cl.addWidget(copy); cl.addStretch(); lower.addWidget(card)
        root.addLayout(lower); root.addStretch()
    def begin_scan(self,total):
        self.import_button.setEnabled(False); self.status.setText("SCANNING"); self.status_detail.setText(f"Found {total} supported file{'s' if total!=1 else ''}. Reading image metadata locally…"); self.progress.setRange(0,max(total,1)); self.progress.setValue(0)
    def set_scan_progress(self,current,total): self.progress.setMaximum(max(total,1)); self.progress.setValue(current); self.status_detail.setText(f"Reading image {current} of {total}…")
    def set_import_summary(self,library_count,result,folder):
        self.import_button.setEnabled(True); self.progress.setValue(self.progress.maximum()); self.status.setText("COMPLETE"); imported,discovered,skipped=result['imported'],result['discovered'],result['skipped']; self.status_detail.setText(f"Imported {imported} readable image{'s' if imported!=1 else ''} from {discovered} supported file{'s' if discovered!=1 else ''}. {skipped} skipped."); self.metric_values['photos'][0].setText(str(library_count)); self.metric_values['photos'][1].setText("Indexed locally — originals untouched"); self.metric_values['last'][0].setText(str(imported)); self.metric_values['last'][1].setText(f"Readable images from {folder}")
    def set_existing_count(self,count):
        self.metric_values['photos'][0].setText(str(count)); self.metric_values['photos'][1].setText("Indexed locally — originals untouched")
