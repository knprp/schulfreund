# src/views/dialogs/select_lesson_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QTableWidget, QTableWidgetItem, QDialogButtonBox,
                           QHeaderView, QMessageBox)
from PyQt6.QtCore import Qt

class SelectLessonDialog(QDialog):
    """Dialog zur Auswahl einer Stunde, zu der eine andere Stunde verschoben wird."""
    
    def __init__(self, parent=None, course_id=None, exclude_date=None):
        """
        Initialisiert den Dialog.
        
        Args:
            parent: Referenz zum Hauptfenster
            course_id: ID des Kurses, dessen Stunden angezeigt werden sollen
            exclude_date: Optional, Datum das ausgeschlossen werden soll (die ursprüngliche Stunde)
        """
        super().__init__(parent)
        self.parent = parent
        self.course_id = course_id
        self.exclude_date = exclude_date
        self.selected_lesson = None
        
        self.setWindowTitle("Stunde auswählen")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        self.setup_ui()
        self.load_lessons()
    
    def setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        layout = QVBoxLayout(self)
        
        # Info-Label
        info_label = QLabel("Wählen Sie die Stunde aus, zu der verschoben werden soll:")
        layout.addWidget(info_label)
        
        # Tabelle mit Stunden
        self.lessons_table = QTableWidget()
        self.lessons_table.setColumnCount(4)
        self.lessons_table.setHorizontalHeaderLabels(["Datum", "Zeit", "Thema", "Status"])
        self.lessons_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.lessons_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # Spaltenbreiten anpassen
        header = self.lessons_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.lessons_table)
        
        # Dialog-Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept_selection)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_lessons(self):
        """Lädt alle Stunden des Kurses in die Tabelle"""
        try:
            if not self.course_id:
                QMessageBox.warning(self, "Fehler", "Kein Kurs ausgewählt.")
                return
            
            # Hole alle Stunden des Kurses
            # Verwende die alte API für Rückwärtskompatibilität
            all_lessons = self.parent.db.get_all_lessons()
            course_lessons = [l for l in all_lessons if l.get('course_id') == self.course_id]
            
            # Sortiere nach Datum und Zeit
            course_lessons.sort(key=lambda x: (x.get('date', ''), x.get('time', '')))
            
            # Filtere die auszuschließende Stunde heraus
            if self.exclude_date:
                course_lessons = [
                    l for l in course_lessons 
                    if l.get('date') != self.exclude_date
                ]
            
            # Fülle Tabelle
            self.lessons_table.setRowCount(len(course_lessons))
            
            for row, lesson in enumerate(course_lessons):
                # Datum
                date_item = QTableWidgetItem(lesson.get('date', ''))
                date_item.setData(Qt.ItemDataRole.UserRole, lesson)
                self.lessons_table.setItem(row, 0, date_item)
                
                # Zeit
                time_item = QTableWidgetItem(lesson.get('time', ''))
                self.lessons_table.setItem(row, 1, time_item)
                
                # Thema
                topic_item = QTableWidgetItem(lesson.get('topic', '-'))
                self.lessons_table.setItem(row, 2, topic_item)
                
                # Status
                status = lesson.get('status', 'normal')
                status_text = {
                    'normal': 'Normal',
                    'cancelled': 'Entfällt',
                    'moved': 'Verschoben',
                    'substituted': 'Vertreten'
                }.get(status, status)
                status_item = QTableWidgetItem(status_text)
                self.lessons_table.setItem(row, 3, status_item)
            
            # Wenn keine Stunden vorhanden
            if len(course_lessons) == 0:
                QMessageBox.information(
                    self, 
                    "Keine Stunden", 
                    "Für diesen Kurs sind keine anderen Stunden verfügbar."
                )
        
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Fehler", 
                f"Fehler beim Laden der Stunden: {str(e)}"
            )
    
    def accept_selection(self):
        """Wird aufgerufen wenn OK geklickt wird"""
        selected_items = self.lessons_table.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(
                self, 
                "Keine Auswahl", 
                "Bitte wählen Sie eine Stunde aus."
            )
            return
        
        # Hole die ausgewählte Stunde aus dem UserRole-Daten
        row = selected_items[0].row()
        date_item = self.lessons_table.item(row, 0)
        self.selected_lesson = date_item.data(Qt.ItemDataRole.UserRole)
        
        if self.selected_lesson:
            self.accept()
        else:
            QMessageBox.warning(
                self, 
                "Fehler", 
                "Konnte die ausgewählte Stunde nicht laden."
            )
    
    def get_selected_lesson(self):
        """Gibt die ausgewählte Stunde zurück"""
        return self.selected_lesson
