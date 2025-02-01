from PyQt6.QtWidgets import QTableView, QHeaderView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor

class DayScheduleView(QTableView):
    def __init__(self, calendar_container):
        super().__init__()
        self.calendar_container = calendar_container
        self.main_window = calendar_container.parent
        self.setup_ui()
        self.doubleClicked.connect(self.on_double_click)
        
    def setup_ui(self):
        # Spaltenüberschriften festlegen
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels([
            "Zeit", "Kurs/Klasse", "Fach", "Thema", "Status"
        ])
        self.setModel(self.model)
        
        # Spaltenbreiten optimieren
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Zeit
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Kurs
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Fach
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Thema
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Status
        
        # Feste Breiten setzen
        self.setColumnWidth(0, 120)  # Zeit
        self.setColumnWidth(1, 150)  # Kurs
        self.setColumnWidth(2, 100)  # Fach
        self.setColumnWidth(4, 80)   # Status
        
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
                status: str, lesson_id: int = None, course_color: str = None, 
                homework: str = None, lesson_status: str = 'normal'):
        """
        Fügt eine neue Stunde zur Tabelle hinzu
        
        Args:
            status: UI-Status (aktuell, kein Thema, kommend, nächste)
            lesson_status: Stunden-Status (normal, cancelled, moved, substituted)
        """
        row = []
        
        # Zeit mit gespeicherter lesson_id
        time_item = QStandardItem(time_slot)
        time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if lesson_id is not None:
            time_item.setData(lesson_id, Qt.ItemDataRole.UserRole)
        row.append(time_item)
        
        # Kurs und Fach mit Hintergrundfarbe
        base_text = course if lesson_status == 'normal' else self.get_status_text(course, lesson_status)
        course_item = QStandardItem(base_text)
        subject_item = QStandardItem(subject)
        
        if course_color:
            color = QColor(course_color)
            # Bei cancelled: mehr Transparenz
            if lesson_status == 'cancelled':
                color.setAlpha(40)
            # Bei moved: Hellgelber Hintergrund
            elif lesson_status == 'moved':
                color = QColor('#FFFFD0')
            brightness = (color.red() * 299 + color.green() * 587 + color.blue() * 114) / 1000
            text_color = QColor('white') if brightness < 128 else QColor('black')
            
            for item in [course_item, subject_item]:
                item.setBackground(color)
                item.setForeground(text_color)
                
        row.append(course_item)
        row.append(subject_item)
        
        # Topic mit Status-Formatierung
        topic_text = topic
        if lesson_status == 'cancelled':
            topic_text = f"⛔ {topic} (entfällt)"
        elif lesson_status == 'moved':
            topic_text = f"→ {topic} (verlegt)"
        elif lesson_status == 'substituted':
            topic_text = f"🔄 {topic} (Vertretung)"
        row.append(QStandardItem(topic_text))
        
        # UI-Status mit Farbkodierung
        status_item = QStandardItem(status)
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if status == "aktuell":
            status_item.setBackground(QColor("#e3f2fd"))
        elif status == "kein Thema":
            status_item.setBackground(QColor("#ffebee"))
        elif status == "kommend":
            status_item.setBackground(QColor("#f1f8e9"))
        elif status == "nächste":
            status_item.setBackground(QColor("#fff3e0"))
        row.append(status_item)
        
        # Hauptzeile zur Tabelle hinzufügen
        main_row = self.model.rowCount()
        self.model.appendRow(row)
        
        # Wenn Hausaufgaben vorhanden, füge Unterzeile hinzu
        if homework and homework.strip():
            hw_row = []
            # Eingerücktes Icon oder Text für Hausaufgaben
            indent_item = QStandardItem("📚 ")  # Emoji mit Leerzeichen
            indent_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            hw_row.append(indent_item)
            
            # Hausaufgaben über Kurs und Fach-Spalte
            hw_item = QStandardItem(homework)
            hw_item.setBackground(QColor("#f5f5f5"))  # Leicht grauer Hintergrund
            hw_row.append(hw_item)
            
            # Leere Items für die restlichen Spalten
            hw_row.extend([QStandardItem(""), QStandardItem(""), QStandardItem("")])
            self.model.appendRow(hw_row)
            # Verbinde die Kurs- und Fach-Spalte für die Hausaufgabenzeile
            self.setSpan(self.model.rowCount()-1, 1, 1, 2)

    def get_status_text(self, text: str, status: str) -> str:
        """Formatiert Text entsprechend des Status"""
        if status == 'cancelled':
            return f"⛔ {text}"
        elif status == 'moved':
            return f"→ {text}"
        elif status == 'substituted':
            return f"🔄 {text}"
        return text
            

    def get_lesson_id_at_position(self, pos):
        """Gibt die lesson_id an der Position zurück oder None"""
        index = self.indexAt(pos)
        if index.isValid():
            # Hole das erste Item der Zeile (Zeit-Spalte)
            time_item = self.model.item(index.row(), 0)
            if time_item:
                return time_item.data(Qt.ItemDataRole.UserRole)
        return None


    def on_double_click(self, index):
        """Handler für Doppelklick auf eine Stunde"""
        # Hole die lesson_id aus der ersten Spalte der Zeile
        time_item = self.model.item(index.row(), 0)
        if time_item:
            lesson_id = time_item.data(Qt.ItemDataRole.UserRole)
            if lesson_id is not None:
                self.show_lesson_details(lesson_id)

    def show_lesson_details(self, lesson_id):
        """Öffnet den Dialog mit den Stundendetails"""
        from src.views.dialogs.lesson_details_dialog import LessonDetailsDialog
        dialog = LessonDetailsDialog(self.main_window, lesson_id)
        dialog.exec()