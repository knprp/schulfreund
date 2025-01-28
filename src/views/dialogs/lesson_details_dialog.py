# src/views/dialogs/lesson_details_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QTextEdit, QPushButton, QTabWidget,
                           QWidget, QMessageBox, QTableWidget, QTableWidgetItem,
                           QComboBox, QCheckBox, QHeaderView, QGroupBox)
from PyQt6.QtCore import Qt
import math

class LessonDetailsDialog(QDialog):
    # Spalten-Konstanten
    COLUMN_NAME = 0
    COLUMN_ATTENDANCE = 1
    COLUMN_GRADE = 2
    COLUMN_REMARK = 3

    def __init__(self, main_window, lesson_id):
        """
        Initialisiert den Dialog.
        
        Args:
            main_window: Referenz zum Hauptfenster (SchoolManagement)
            lesson_id: ID der Stunde
        """
        QDialog.__init__(self)  
        self.main_window = main_window  # Dies ist die direkte Referenz zum Hauptfenster
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
        date_time = QLabel(f"<b>{self.lesson['date']} - {self.lesson['time']}</b>")
        header.addWidget(date_time)
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
        self.competencies_container = QVBoxLayout()
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
        self.update_competencies_label()
        students_layout.addWidget(self.competencies_label)
        
        # Tabelle für Schüler
        self.students_table = QTableWidget()
        self.students_table.setColumnCount(4)
        self.students_table.setHorizontalHeaderLabels([
            "Name", "Anwesenheit", "Note", "Bemerkung"
        ])

        # Spaltenbreiten anpassen
        header = self.students_table.horizontalHeader()
        header.setSectionResizeMode(self.COLUMN_NAME, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COLUMN_ATTENDANCE, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(self.COLUMN_GRADE, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(self.COLUMN_REMARK, QHeaderView.ResizeMode.Stretch)

        # Fixe Breiten setzen
        self.students_table.setColumnWidth(self.COLUMN_ATTENDANCE, 100)
        self.students_table.setColumnWidth(self.COLUMN_GRADE, 80)
        
        students_layout.addWidget(self.students_table)
        tab_widget.addTab(students_tab, "Schüler")

        layout.addWidget(tab_widget)

        # Notengruppe
        grade_group = QGroupBox("Noteneintrag")
        grade_layout = QVBoxLayout()

        # Typ der Note
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Bewertungstyp:"))
        self.assessment_type = QComboBox()
        self.load_assessment_types()
        type_layout.addWidget(self.assessment_type)
        grade_layout.addLayout(type_layout)

        # Name/Beschreibung der Note
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Bezeichnung:"))
        self.assessment_name = QLineEdit()
        self.assessment_name.setPlaceholderText("z.B. Vokabeltest Unit 5")
        name_layout.addWidget(self.assessment_name)
        grade_layout.addLayout(name_layout)

        grade_group.setLayout(grade_layout)
        general_layout.addWidget(grade_group)

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
            # Prüfe ob es Noten gibt und hole die erste für Typ/Namen
            cursor = self.main_window.db.execute(
                """SELECT DISTINCT a.assessment_type_id, a.topic 
                FROM assessments a
                WHERE a.lesson_id = ? 
                LIMIT 1""",
                (self.lesson_id,)
            )
            assessment = cursor.fetchone()
            if assessment:
                # Setze Bewertungstyp
                type_idx = self.assessment_type.findData(assessment['assessment_type_id'])
                if type_idx >= 0:
                    self.assessment_type.setCurrentIndex(type_idx)
                    
                # Setze Namen/Bezeichnung
                if assessment['topic']:
                    self.assessment_name.setText(assessment['topic'])

        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Daten: {str(e)}")
        
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
            print("DEBUG Save - Starting save_data()") # NEU
            
            # Allgemeine Stundendaten
            print("DEBUG Save - Updating lesson data") # NEU
            self.main_window.db.update_lesson(
                self.lesson_id,
                {
                    'topic': self.topic.text().strip(),
                    'homework': self.homework.toPlainText().strip()
                }
            )

            # Kompetenzen
            print("DEBUG Save - Starting competencies update") # NEU
            self.main_window.db.execute(
                "DELETE FROM lesson_competencies WHERE lesson_id = ?",
                (self.lesson_id,)
            )
            
            # Schülerverarbeitung
            print(f"DEBUG Save - Starting student processing, rows: {self.students_table.rowCount()}") # NEU
            
            # Assessment Type Info
            assessment_type_id = self.assessment_type.currentData()
            print(f"DEBUG Save - Assessment type ID: {assessment_type_id}") # NEU
            
            for row in range(self.students_table.rowCount()):
                print(f"DEBUG Save - Processing row {row}") # NEU
                student_item = self.students_table.item(row, self.COLUMN_NAME)
                student_id = student_item.data(Qt.ItemDataRole.UserRole)
                print(f"DEBUG Save - Student ID: {student_id}") # NEU

                # Anwesenheit
                attendance_checkbox = self.students_table.cellWidget(row, self.COLUMN_ATTENDANCE)
                print(f"DEBUG Save - Attendance checked: {attendance_checkbox.isChecked()}") # NEU
                    
                # Note
                if assessment_type_id:
                    print("DEBUG Save - Processing grade")
                    grade_combo = self.students_table.cellWidget(row, self.COLUMN_GRADE)
                    grade_str = grade_combo.currentText()
                    print(f"DEBUG Save - Raw grade string: '{grade_str}'")
                    
                    if grade_str:
                        numeric_grade = self.grade_to_number(grade_str)
                        print(f"DEBUG Save - Converting {grade_str} to numeric: {numeric_grade}")
                        
                        # Assessment-Name aus dem UI-Element holen
                        assessment_name = self.assessment_name.text().strip()
                        print(f"DEBUG Save - Assessment name: {assessment_name}")  # NEU
                        
                        # Assessment-Daten zusammenstellen
                        assessment_data = {
                            'student_id': student_id,
                            'course_id': self.lesson['course_id'],
                            'assessment_type_id': assessment_type_id,
                            'grade': numeric_grade,
                            'date': self.lesson['date'],
                            'lesson_id': self.lesson_id,
                            'topic': assessment_name
                        }
                        print(f"DEBUG Save - About to save assessment data: {assessment_data}")
                        
                        try:
                            self.main_window.db.add_assessment(assessment_data)
                            print(f"DEBUG Save - Successfully saved assessment")
                        except Exception as e:
                            print(f"DEBUG Save - Error saving assessment: {str(e)}")
                
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
                self.students_table.setItem(row, self.COLUMN_NAME, name_item)
                
                # Anwesenheit
                attendance = QCheckBox()
                attendance.setChecked(True)
                self.students_table.setCellWidget(row, self.COLUMN_ATTENDANCE, attendance)
                
                # Note
                grade_combo = QComboBox()
                self.setup_grade_combo(grade_combo)
                grade_combo.setEnabled(True)
                self.students_table.setCellWidget(row, self.COLUMN_GRADE, grade_combo)
                
                # Bemerkung
                remark = QLineEdit()
                self.students_table.setCellWidget(row, self.COLUMN_REMARK, remark)
                
                # Lade existierende Note wenn vorhanden
                try:
                    assessment = self.main_window.db.get_lesson_assessment(
                        student['id'], 
                        self.lesson_id
                    )
                    print(f"DEBUG Load - Raw assessment data: {assessment}")  # Neue Debug-Zeile
                    
                    if assessment:
                        grade_str = self.number_to_grade(assessment['grade'])
                        print(f"DEBUG Load - Converting {assessment['grade']} to string: {grade_str}")  # Neue Debug-Zeile
                        
                        index = grade_combo.findText(grade_str)
                        print(f"DEBUG Load - Found index {index} for grade {grade_str}")  # Neue Debug-Zeile
                        
                        if index >= 0:
                            grade_combo.setCurrentIndex(index)
                            print(f"DEBUG Load - Set combobox to index {index}")  # Neue Debug-Zeile
                        else:
                            print(f"DEBUG Load - WARNING: Grade string '{grade_str}' not found in combo items!")  # Neue Debug-Zeile
                            print(f"DEBUG Load - Available items: {[grade_combo.itemText(i) for i in range(grade_combo.count())]}")  # Neue Debug-Zeile
                except Exception as e:
                    print(f"DEBUG Load - Error loading grade: {str(e)}")
                    print(f"DEBUG Load - Full error details: ", exc_info=True)  # Neue Debug-Zeile
                    
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Schüler: {str(e)}")

    def setup_grade_combo(self, combo: QComboBox):
        """Richtet die Noten-ComboBox ein"""
        combo.addItem("")  # Leere Auswahl als erste Option
        
        try:
            # Hole das Notensystem für den Kurs
            grading_system = self.main_window.db.get_course_grading_system(self.lesson['course_id'])
            if not grading_system:
                # Wenn kein Notensystem definiert ist, nur leere Auswahl anbieten
                QMessageBox.warning(self, "Warnung", 
                                "Kein Notensystem für diesen Kurs definiert!")
                return
                
            # Generiere mögliche Noten basierend auf dem System
            current = grading_system['min_grade']
            grades = []
            while current <= grading_system['max_grade']:
                grades.append(f"{current:.1f}")
                current = round(current + grading_system['step_size'], 2)
                
            combo.addItems(grades)
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", 
                            "Fehler beim Laden des Notensystems.\n"
                            "Bitte definieren Sie zuerst ein Notensystem für diesen Kurs.")

    def on_grade_changed(self, index: int, row: int):
        """Handler für Notenänderungen"""
        combo = self.students_table.cellWidget(row, self.COLUMN_GRADE)
        if not combo:  
            return
            
        attendance_checkbox = self.students_table.cellWidget(row, self.COLUMN_ATTENDANCE)
        if not attendance_checkbox:  
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
                combo.blockSignals(True)
                combo.setCurrentIndex(0)  # Zurück zu "keine Note"
                combo.blockSignals(False)

    def add_competency_row(self, is_first_row=False):
        """Fügt eine neue Kompetenzauswahl-Zeile hinzu"""
        row_layout = QHBoxLayout()
        
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
        """Entfernt eine Kompetenzauswahl-Zeile"""
        while row_layout.count():
            item = row_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        self.competencies_container.removeItem(row_layout)
        row_layout.deleteLater()
        self.update_competencies_label()

    def load_competencies_for_subject(self, combo: QComboBox):
        """Lädt die verfügbaren Kompetenzen für das Fach"""
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
        if not selected_id:  
            return
            
        for i in range(self.competencies_container.count()):
            layout_item = self.competencies_container.itemAt(i)
            if layout_item and layout_item.layout():
                combo = layout_item.layout().itemAt(0).widget()
                if combo != changed_combo and combo.currentData() == selected_id:
                    QMessageBox.warning(self, "Doppelte Auswahl", 
                                      "Diese Kompetenz wurde bereits ausgewählt!")
                    changed_combo.setCurrentIndex(0)
                    return
        self.update_competencies_label()

    def update_competencies_label(self):
        """Aktualisiert das Label mit den ausgewählten Kompetenzen"""
        selected_comps = []
        for i in range(self.competencies_container.count()):
            layout_item = self.competencies_container.itemAt(i)
            if layout_item and layout_item.layout():
                combo = layout_item.layout().itemAt(0).widget()
                if combo.currentData():
                    selected_comps.append(combo.currentText())
        
        if selected_comps:
            text = "<b>Zu bewertende Kompetenzen:</b><br>" + "<br>".join(f"• {comp}" for comp in selected_comps)
        else:
            text = "<b>Keine Kompetenzen ausgewählt</b>"
        
        self.competencies_label.setText(text)

    def load_assessment_types(self):
        """Lädt die verfügbaren Bewertungstypen für den Kurs"""
        try:
            self.assessment_type.clear()
            self.assessment_type.addItem("", None)  # Leere Auswahl
            
            types = self.main_window.db.get_assessment_types(self.lesson['course_id'])
            for type_data in types:
                self.assessment_type.addItem(type_data['name'], type_data['id'])
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", 
                               f"Fehler beim Laden der Bewertungstypen: {str(e)}")

    def setup_assessment_type_combo(self, row: int) -> QComboBox:
        """Erstellt und konfiguriert eine ComboBox für Bewertungstypen"""
        combo = QComboBox()
        combo.addItem("", None)  # Leere Auswahl
        
        try:
            types = self.main_window.db.get_assessment_types(self.lesson['course_id'])
            for type_data in types:
                combo.addItem(type_data['name'], type_data['id'])
                
            combo.currentIndexChanged.connect(
                lambda idx, r=row: self.on_assessment_type_changed(idx, r)
            )
            
        except Exception as e:
            print(f"Fehler beim Laden der Bewertungstypen: {str(e)}")
            
        return combo

    def on_assessment_type_changed(self, index: int, row: int):
        """Handler für Änderungen am Bewertungstyp"""
        combo = self.students_table.cellWidget(row, self.COLUMN_GRADE)
        if not combo:
            return
            
        # Wenn ein Typ ausgewählt wurde, aktiviere die Notenauswahl
        combo.setEnabled(index > 0)

    def grade_to_number(self, grade_str: str) -> float:
        """Wandelt eine Note aus der ComboBox in einen numerischen Wert um."""
        if not grade_str:
            return None
            
        try:
            # Versuche erst direkt den String als Zahl zu parsen
            # für Formate wie "1.0", "2.0" etc.
            return float(grade_str)
                
        except ValueError:
            # Wenn das nicht klappt, versuche die +/- Notation zu interpretieren
            base = float(grade_str[0])
            if len(grade_str) > 1:
                if grade_str[1] == '+':
                    base -= 0.33
                elif grade_str[1] == '-':
                    base += 0.33
                    
            return round(base, 2)

    def _standard_grade_to_number(self, grade_str: str) -> float:
        """Standard-Konvertierung für 1-6 Notensystem."""
        if not grade_str:
            return None
            
        base = float(grade_str[0])
        if len(grade_str) > 1:
            if grade_str[1] == '+':
                base -= 0.33
            elif grade_str[1] == '-':
                base += 0.33
                
        return round(base, 2)

    def number_to_grade(self, number: float) -> str:
        """Wandelt einen numerischen Notenwert in einen String für die ComboBox um."""
        return f"{float(number):.1f}"

    def _standard_number_to_grade(self, number: float) -> str:
        """Standard-Konvertierung für 1-6 Notensystem."""
        number = round(number, 2)
        base = math.ceil(number)
        diff = base - number
        
        if diff > 0.3:
            return f"{base}+"
        elif diff < 0.01:
            return str(base)
        else:
            return f"{base}-"