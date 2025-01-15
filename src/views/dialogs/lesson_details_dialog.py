# src/views/dialogs/lesson_details_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QTextEdit, QPushButton, QTabWidget,
                           QWidget, QMessageBox, QTableWidget, QTableWidgetItem,
                           QComboBox, QCheckBox, QHeaderView)
from PyQt6.QtCore import Qt
import math

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
        
        # Tab: Schüler
        students_tab = QWidget()
        students_layout = QVBoxLayout(students_tab)
        
        # Tabelle für Schüler
        self.students_table = QTableWidget()
        self.students_table.setColumnCount(4)
        self.students_table.setHorizontalHeaderLabels([
            "Name", "Anwesenheit", "Note", "Bemerkung"
        ])
        
        # Spaltenbreiten anpassen
        header = self.students_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)    # Anwesenheit
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)    # Note
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Bemerkung
        
        students_layout.addWidget(self.students_table)
        tab_widget.addTab(students_tab, "Schüler")

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
        
        # Lade Schüler und deren Anwesenheit
        self.load_students()
        
        # Markiere abwesende Schüler
        try:
            absent_students = self.main_window.db.get_absent_students(self.lesson_id)
            
            # Durchlaufe alle Zeilen der Tabelle
            for row in range(self.students_table.rowCount()):
                student_item = self.students_table.item(row, 0)
                student_id = student_item.data(Qt.ItemDataRole.UserRole)
                
                # Hole die Checkbox
                attendance_checkbox = self.students_table.cellWidget(row, 1)
                
                # Setze Checkbox basierend auf Anwesenheit
                attendance_checkbox.setChecked(student_id not in absent_students)
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Anwesenheit: {str(e)}")
            # Notizen später...

    def grade_to_number(self, grade_str: str) -> float:
        """Wandelt eine Note aus der ComboBox in einen numerischen Wert um."""
        if not grade_str:  # Leere Auswahl
            return None
            
        # Basisnote
        base = float(grade_str[0])
        
        # Tendenz
        if len(grade_str) > 1:
            if grade_str[1] == '+':
                base -= 0.33
            elif grade_str[1] == '-':
                base += 0.33
        
        return round(base, 2)

    def number_to_grade(self, number: float) -> str:
        """Wandelt einen numerischen Notenwert in einen Anzeige-String um.
        
        0.67 -> "1+"
        1.0  -> "1"
        1.33 -> "1-"
        """
        # Runde auf 2 Dezimalstellen um Fließkomma-Ungenauigkeiten zu vermeiden
        number = round(number, 2)
        
        # Basisnote ist die aufgerundete Zahl
        base = math.ceil(number)
        
        # Differenz zur Basisnote bestimmt + oder -
        diff = base - number
        
        if diff > 0.3:  # z.B. 1 - 0.67 = 0.33 -> "1+"
            return f"{base}+"
        elif diff < 0.01:  # Fast 0 -> glatte Note
            return str(base)
        else:  # z.B. 1 - 1.33 = -0.33 -> "1-"
            return f"{base}-"

    def save_data(self):
        """Speichert die Änderungen"""
        try:
            # Bestehender Code für allgemeine Stundendaten...
            self.main_window.db.update_lesson(
                self.lesson_id,
                {
                    'topic': self.topic.text().strip(),
                    'homework': self.homework.toPlainText().strip()
                }
            )
            
            # Speichere Anwesenheit und Noten
            for row in range(self.students_table.rowCount()):
                student_item = self.students_table.item(row, 0)
                student_id = student_item.data(Qt.ItemDataRole.UserRole)
                
                # Anwesenheit
                attendance_checkbox = self.students_table.cellWidget(row, 1)
                if attendance_checkbox.isChecked():
                    self.main_window.db.mark_student_present(self.lesson_id, student_id)
                else:
                    self.main_window.db.mark_student_absent(self.lesson_id, student_id)
                
                # Note
                grade_combo = self.students_table.cellWidget(row, 2)
                grade_str = grade_combo.currentText()
                
                if grade_str:  # Note wurde ausgewählt
                    numeric_grade = self.grade_to_number(grade_str)
                    self.main_window.db.add_assessment({
                        'student_id': student_id,
                        'course_id': self.lesson['course_id'],
                        'assessment_type_id': 14,
                        'grade': numeric_grade,
                        'date': self.lesson['date'],
                        'lesson_id': self.lesson_id
                    })
                else:  # Note wurde gelöscht
                    self.main_window.db.delete_assessment(
                        student_id=student_id,
                        lesson_id=self.lesson_id
                    )
            
            self.accept()
            
            # Liste aktualisieren
            self.main_window.list_manager.update_all(
                self.main_window.calendar_container.get_selected_date()
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern: {str(e)}")

    def load_students(self):
        """Lädt die Schüler des Kurses in die Tabelle"""
        try:
            # Hole aktives Semester
            semester = self.main_window.db.get_semester_dates()
            if not semester:
                raise ValueError("Kein aktives Semester gefunden")

            # Hole semester_id aus der Historie
            cursor = self.main_window.db.execute(
                """SELECT id FROM semester_history 
                WHERE start_date = ? AND end_date = ?""",
                (semester['semester_start'], semester['semester_end'])
            )
            semester_result = cursor.fetchone()
            if not semester_result:
                raise ValueError("Aktives Semester nicht in der Historie gefunden")

            # Hole alle Schüler des Kurses für das aktuelle Semester
            students = self.main_window.db.get_students_by_course(
                self.lesson['course_id'], 
                semester_result['id']
            )

            # Fülle die Tabelle
            self.students_table.setRowCount(len(students))
            for row, student in enumerate(students):
                # Name
                name_item = QTableWidgetItem(f"{student['last_name']}, {student['first_name']}")
                name_item.setData(Qt.ItemDataRole.UserRole, student['id'])
                self.students_table.setItem(row, 0, name_item)
                
                # Anwesenheit
                attendance = QCheckBox()
                attendance.setChecked(True)  # Standard: anwesend
                self.students_table.setCellWidget(row, 1, attendance)
                
                # Note
                grade_combo = QComboBox()
                self.setup_grade_combo(grade_combo)
                
                # Prüfe ob es bereits eine Note gibt
                print(f"DEBUG: Loading assessment for student {student['id']}")

                try:
                    assessment = self.main_window.db.get_lesson_assessment(
                        student['id'], 
                        self.lesson_id
                    )
                    print(f"DEBUG: Got assessment: {assessment}")  # Neue Debug-Ausgabe
                    
                    if assessment:
                        grade_str = self.number_to_grade(assessment['grade'])
                        print(f"DEBUG: Converted to grade string: {grade_str}")  # Neue Debug-Ausgabe
                        index = grade_combo.findText(grade_str)
                        print(f"DEBUG: Found at index: {index}")  # Neue Debug-Ausgabe
                        if index >= 0:
                            grade_combo.setCurrentIndex(index)
                except Exception as e:
                    print(f"DEBUG: Error loading grade: {str(e)}")  # Erweiterte Debug-Ausgabe
                    
                self.students_table.setCellWidget(row, 2, grade_combo)
                    
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Schüler: {str(e)}")

    def setup_grade_combo(self, combo: QComboBox):
        """Richtet die Noten-Combobox ein"""
        # Keine Note als erste Option
        combo.addItem("")
        # Zunächst nur Unterstufen-Noten
        grades = [
            "", "1+", "1", "1-", "2+", "2", "2-", "3+", "3", "3-",
            "4+", "4", "4-", "5+", "5", "5-", "6"
        ]
        combo.addItems(grades)