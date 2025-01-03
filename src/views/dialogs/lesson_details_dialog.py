# src/views/dialogs/lesson_details_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QTextEdit, QPushButton, QTabWidget,
                           QWidget, QMessageBox) 
from PyQt6.QtCore import Qt

class LessonDetailsDialog(QDialog):
    def __init__(self, main_window, lesson_id):
        """
        Initialisiert den Dialog.
        
        Args:
            main_window: Referenz zum Hauptfenster (SchoolManagement)
            lesson_id: ID der Stunde
        """
        QDialog.__init__(self)  # Korrekte Initialisierung
        self.main_window = main_window
        self.lesson_id = lesson_id
        self.lesson = self.main_window.db.get_lesson(lesson_id)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        self.setWindowTitle("Stundendetails")
        self.setMinimumWidth(600)
        layout = QVBoxLayout(self)

        # Kopfbereich mit Basisinformationen
        header = QHBoxLayout()
        # Datum und Uhrzeit
        date_time = QLabel(f"<b>{self.lesson['date']} - {self.lesson['time']}</b>")
        header.addWidget(date_time)
        # Kurs/Klasse und Fach
        course = QLabel(f"{self.lesson['course_name']} - {self.lesson['subject']}")
        header.addWidget(course)
        layout.addLayout(header)

        # Tabs für verschiedene Bereiche
        tab_widget = QTabWidget()
        
        # Tab: Allgemein
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # Thema
        general_layout.addWidget(QLabel("Thema:"))
        self.topic = QLineEdit()
        general_layout.addWidget(self.topic)
        
        # Hausaufgaben
        general_layout.addWidget(QLabel("Hausaufgaben:"))
        self.homework = QTextEdit()
        general_layout.addWidget(self.homework)
        
        # Notizen
        general_layout.addWidget(QLabel("Notizen:"))
        self.notes = QTextEdit()
        general_layout.addWidget(self.notes)
        
        tab_widget.addTab(general_tab, "Allgemein")
        
        # Tab: Schüler (Platzhalter für später)
        students_tab = QWidget()
        tab_widget.addTab(students_tab, "Schüler")
        
        # Tab: Noten (Platzhalter für später)
        grades_tab = QWidget()
        tab_widget.addTab(grades_tab, "Noten")

        layout.addWidget(tab_widget)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Speichern")
        save_button.clicked.connect(self.save_data)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("Abbrechen")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)

    def load_data(self):
        """Lädt die Daten der Stunde in den Dialog"""
        self.topic.setText(self.lesson.get('topic', ''))
        self.homework.setText(self.lesson.get('homework', ''))
        # Notizen später...

    def save_data(self):
        """Speichert die Änderungen"""
        try:
            self.main_window.db.update_lesson(
                self.lesson_id,
                {
                    'topic': self.topic.text().strip(),
                    'homework': self.homework.toPlainText().strip()
                    # Weitere Felder später...
                }
            )
            self.accept()
            
            # Liste aktualisieren
            self.main_window.list_manager.update_all(
                self.main_window.calendar_container.get_selected_date()
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern: {str(e)}")