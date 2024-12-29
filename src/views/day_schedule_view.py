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
        
    def add_separator(self, text: str):
        """Fügt eine Trennzeile in die Tabelle ein"""
        separator_item = QStandardItem(text)
        separator_item.setBackground(QColor("#f0f0f0"))  # Hellgrauer Hintergrund
        separator_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # Zentriert
        separator_item.setFlags(separator_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)  # Nicht auswählbar
        
        # Schrift fett machen
        font = separator_item.font()
        font.setBold(True)
        separator_item.setFont(font)
        
        row = self.model.rowCount()
        self.model.appendRow(separator_item)
        
        # Setze columnSpan über alle Spalten
        self.setSpan(row, 0, 1, self.model.columnCount())

    def add_lesson(self, time_slot: str, course: str, subject: str, topic: str, 
                status: str, lesson_id: int = None, course_color: str = None):
        """Fügt eine neue Stunde zur Tabelle hinzu"""
        row = []
        
        # Zeit mit gespeicherter lesson_id
        time_item = QStandardItem(time_slot)
        time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if lesson_id is not None:
            time_item.setData(lesson_id, Qt.ItemDataRole.UserRole)
        row.append(time_item)
        
        # Kurs und Fach mit Hintergrundfarbe
        course_item = QStandardItem(course)
        subject_item = QStandardItem(subject)
        
        if course_color:
            color = QColor(course_color)
            # Berechne Helligkeit (0-255)
            brightness = (color.red() * 299 + color.green() * 587 + color.blue() * 114) / 1000
            
            # Wenn Farbe zu dunkel (Helligkeit < 128), setze Text auf weiß
            text_color = QColor('white') if brightness < 128 else QColor('black')
            
            # Setze Hintergrund- und Textfarbe für Kurs und Fach
            for item in [course_item, subject_item]:
                item.setBackground(color)
                item.setForeground(text_color)
        
        row.append(course_item)
        row.append(subject_item)
        row.append(QStandardItem(topic))
        
        # Status mit Farbkodierung
        status_item = QStandardItem(status)
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if status == "aktuell":
            status_item.setBackground(QColor("#e3f2fd"))  # Helles Blau
        elif status == "kein Thema":
            status_item.setBackground(QColor("#ffebee"))  # Helles Rot
        elif status == "kommend":
            status_item.setBackground(QColor("#f1f8e9"))  # Helles Grün
        elif status == "nächste":
            status_item.setBackground(QColor("#fff3e0"))  # Helles Orange
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