from PyQt6.QtWidgets import QTableView, QHeaderView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor

class DayScheduleView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        # Spaltenüberschriften festlegen
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels([
            "Zeit", "Kurs/Klasse", "Fach", "Thema", "Status"
        ])
        self.setModel(self.model)
        
        # Spaltenbreiten einstellen
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Zeit
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Kurs
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Fach
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)          # Thema
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Status
        
        # Weitere Einstellungen
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.setSortingEnabled(True)
        
        # Zeilen-Indices ausblenden
        self.verticalHeader().setVisible(False)
        
        # Style
        self.setStyleSheet("""
            QTableView {
                gridline-color: #d0d0d0;
                selection-background-color: #e0e0e0;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                padding: 4px;
            }
        """)

    def clear_schedule(self):
        """Leert die Tabelle"""
        self.model.setRowCount(0)
        
    def add_lesson(self, time_slot: str, course: str, subject: str, topic: str, 
                  status: str, lesson_id: int = None):
        """Fügt eine neue Stunde zur Tabelle hinzu"""
        row = []
        
        # Zeit mit gespeicherter lesson_id
        time_item = QStandardItem(time_slot)
        if lesson_id is not None:
            time_item.setData(lesson_id, Qt.ItemDataRole.UserRole)
        row.append(time_item)
        
        # Weitere Spalten
        row.append(QStandardItem(course))
        row.append(QStandardItem(subject))
        row.append(QStandardItem(topic))
        
        # Status mit Farbkodierung
        status_item = QStandardItem(status)
        if status == "aktuell":
            status_item.setBackground(QColor("#e3f2fd"))  # Helles Blau
        elif status == "kein Thema":
            status_item.setBackground(QColor("#ffebee"))  # Helles Rot
        elif status == "kommend":
            status_item.setBackground(QColor("#f1f8e9"))  # Helles Grün
        row.append(status_item)
        
        # Zeile zur Tabelle hinzufügen
        self.model.appendRow(row)

    def get_lesson_id_at_position(self, pos):
        """Gibt die lesson_id an der Position zurück oder None"""
        index = self.indexAt(pos)
        if index.isValid():
            # Hole das erste Item der Zeile (Zeit-Spalte)
            time_item = self.model.item(index.row(), 0)
            if time_item:
                return time_item.data(Qt.ItemDataRole.UserRole)
        return None