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

        # Kompetenzen
        competencies_layout = QVBoxLayout()
        competencies_layout.addWidget(QLabel("Kompetenzen:"))

        # Container für die Kompetenz-Auswahl
        self.competencies_container = QVBoxLayout()

        # Erste Kompetenz-Zeile hinzufügen
        self.add_competency_row(is_first_row=True)

        # Plus-Button für weitere Kompetenzen
        add_competency_button = QPushButton("+")
        add_competency_button.clicked.connect(self.add_competency_row)
        add_competency_button.setMaximumWidth(30)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(add_competency_button)

        competencies_layout.addLayout(self.competencies_container)
        competencies_layout.addLayout(button_layout)
        general_layout.addLayout(competencies_layout)

        
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

        # Label für ausgewählte Kompetenzen
        self.competencies_label = QLabel()
        self.update_competencies_label()  # Initial Label setzen
        students_layout.addWidget(self.competencies_label)
        
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

        self.topic.setText(self.lesson.get('topic', ''))
        self.homework.setText(self.lesson.get('homework', ''))
        
        # Kompetenzen laden
        try:
            # Alle bestehenden Kompetenz-Reihen entfernen (außer der ersten)
            while self.competencies_container.count() > 1:
                layout_item = self.competencies_container.takeAt(self.competencies_container.count() - 1)
                if layout_item and layout_item.layout():
                    self.remove_competency_row(layout_item.layout())

            # Kompetenzen der Stunde laden
            cursor = self.main_window.db.execute(
                """SELECT c.* FROM competencies c
                JOIN lesson_competencies lc ON c.id = lc.competency_id
                WHERE lc.lesson_id = ?
                ORDER BY c.area, c.description""",
                (self.lesson_id,)
            )
            competencies = cursor.fetchall()
            
            # Erste ComboBox aktualisieren/befüllen wenn Kompetenzen vorhanden
            if competencies:
                first_comp = competencies[0]
                first_combo = self.competencies_container.itemAt(0).layout().itemAt(0).widget()
                # Index der ersten Kompetenz in der ComboBox finden
                for i in range(first_combo.count()):
                    if first_combo.itemData(i) == first_comp['id']:
                        first_combo.setCurrentIndex(i)
                        break
            
            # Weitere Kompetenzen in neue Reihen einfügen
            for comp in competencies[1:]:  # Starte bei der zweiten Kompetenz
                self.add_competency_row()  # Neue Reihe hinzufügen
                # Die gerade hinzugefügte ComboBox holen (letzte Reihe)
                row_layout = self.competencies_container.itemAt(self.competencies_container.count() - 1).layout()
                combo = row_layout.itemAt(0).widget()
                # Richtige Kompetenz auswählen
                for i in range(combo.count()):
                    if combo.itemData(i) == comp['id']:
                        combo.setCurrentIndex(i)
                        break
                        
        except Exception as e:
            QMessageBox.critical(self, "Fehler", 
                            f"Fehler beim Laden der Kompetenzen: {str(e)}")
        
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
        try:
            # Bestehender Code für allgemeine Stundendaten
            self.main_window.db.update_lesson(
                self.lesson_id,
                {
                    'topic': self.topic.text().strip(),
                    'homework': self.homework.toPlainText().strip()
                }
            )

            # Kompetenzen der Stunde aktualisieren
            # Zuerst alle bestehenden Verknüpfungen löschen
            self.main_window.db.execute(
                "DELETE FROM lesson_competencies WHERE lesson_id = ?",
                (self.lesson_id,)
            )
            
            # Neue Kompetenzen sammeln und speichern
            for i in range(self.competencies_container.count()):
                layout_item = self.competencies_container.itemAt(i)
                if layout_item and layout_item.layout():
                    row_layout = layout_item.layout()
                    combo_item = row_layout.itemAt(0)
                    if combo_item and combo_item.widget():
                        combo = combo_item.widget()
                        competency_id = combo.currentData()
                        if competency_id:
                            self.main_window.db.add_lesson_competency(
                                self.lesson_id, 
                                competency_id
                            )

            # Bestehender Code für Anwesenheit und Noten
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
                # Verbinde Signal mit Row-Information
                grade_combo.currentIndexChanged.connect(
                    lambda idx, r=row: self.on_grade_changed(idx, r)
                )
                
                # Prüfe ob es bereits eine Note gibt
                try:
                    assessment = self.main_window.db.get_lesson_assessment(
                        student['id'], 
                        self.lesson_id
                    )                   
                    if assessment:
                        grade_str = self.number_to_grade(assessment['grade'])
                        index = grade_combo.findText(grade_str)
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
        # Unterstufen-Noten
        grades = [
            "1+", "1", "1-", "2+", "2", "2-", "3+", "3", "3-",
            "4+", "4", "4-", "5+", "5", "5-", "6"
        ]
        combo.addItems(grades)


    def on_grade_changed(self, index: int, row: int):
        """Handler für Notenänderungen"""
        # Hole die ComboBox für diese Zeile direkt aus der Tabelle
        combo = self.students_table.cellWidget(row, 2)
        if not combo:  # Sicherheitscheck
            return
            
        attendance_checkbox = self.students_table.cellWidget(row, 1)
        if not attendance_checkbox:  # Sicherheitscheck
            return
            
        grade_str = combo.currentText()
        
        if grade_str and not attendance_checkbox.isChecked():
            if QMessageBox.question(
                self,
                "Abwesender Schüler",
                "Der Schüler ist als abwesend markiert. Möchten Sie trotzdem eine Note vergeben?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            ) == QMessageBox.StandardButton.No:
                # Blockiere temporär das Signal um Endlosschleife zu vermeiden
                combo.blockSignals(True)
                combo.setCurrentIndex(0)  # Setze zurück auf "keine Note"
                combo.blockSignals(False)

    # Neue Methode für das Hinzufügen einer Kompetenz-Zeile
    def add_competency_row(self, is_first_row=False):
        """Fügt eine neue Kompetenzauswahl-Zeile hinzu"""
        row_layout = QHBoxLayout()
        
        # ComboBox für Kompetenzen
        combo = QComboBox()
        combo.currentIndexChanged.connect(lambda: self.check_duplicate_selection(combo))
        self.load_competencies_for_subject(combo)
        
        row_layout.addWidget(combo)
        
        if not is_first_row:
            remove_btn = QPushButton("-")
            remove_btn.setMaximumWidth(30)
            remove_btn.clicked.connect(lambda: self.remove_competency_row(row_layout))
            row_layout.addWidget(remove_btn)
        
        self.competencies_container.addLayout(row_layout)


    def on_competency_selected(self, changed_combo):
        """Handler für Kompetenzauswahl"""
        self.update_competency_combos(exclude_combo=changed_combo)

    def remove_competency_row(self, row_layout):
        # Entferne alle Widgets aus dem Layout
        while row_layout.count():
            item = row_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Entferne das Layout selbst
        self.competencies_container.removeItem(row_layout)
        row_layout.deleteLater()
        # Label nach dem Entfernen aktualisieren
        self.update_competencies_label()

    def load_competencies_for_subject(self, combo: QComboBox):
        try:
            subject = self.lesson.get('subject')
            if subject:
                combo.clear()
                combo.addItem("", None)  # Leere Auswahl als erste Option
                competencies = self.main_window.db.get_competencies_by_subject(subject)
                for comp in competencies:
                    display_text = f"{comp['area']}: {comp['description']}"
                    combo.addItem(display_text, comp['id'])
        except Exception as e:
            QMessageBox.critical(self, "Fehler", 
                            f"Fehler beim Laden der Kompetenzen: {str(e)}")

    def check_duplicate_selection(self, changed_combo):
        """Prüft ob die gewählte Kompetenz bereits ausgewählt ist"""
        selected_id = changed_combo.currentData()
        if not selected_id:  # Leere Auswahl ist immer okay
            return
            
        # Prüfe alle anderen ComboBoxen
        for i in range(self.competencies_container.count()):
            layout_item = self.competencies_container.itemAt(i)
            if layout_item and layout_item.layout():
                combo = layout_item.layout().itemAt(0).widget()
                if combo != changed_combo and combo.currentData() == selected_id:
                    QMessageBox.warning(self, "Doppelte Auswahl", 
                                    "Diese Kompetenz wurde bereits ausgewählt!")
                    changed_combo.setCurrentIndex(0)  # Zurück zur leeren Auswahl
                    return
        # Label aktualisieren wenn keine Duplikate gefunden wurden
        self.update_competencies_label()

    def update_competencies_label(self):
        """Aktualisiert das Label mit den ausgewählten Kompetenzen"""
        selected_comps = []
        for i in range(self.competencies_container.count()):
            layout_item = self.competencies_container.itemAt(i)
            if layout_item and layout_item.layout():
                combo = layout_item.layout().itemAt(0).widget()
                if combo.currentData():  # Wenn eine Kompetenz ausgewählt ist
                    selected_comps.append(combo.currentText())
        
        if selected_comps:
            text = "<b>Zu bewertende Kompetenzen:</b><br>" + "<br>".join(f"• {comp}" for comp in selected_comps)
        else:
            text = "<b>Keine Kompetenzen ausgewählt</b>"
        
        self.competencies_label.setText(text)