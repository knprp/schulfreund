# src/views/dialogs/course_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QDialogButtonBox, QPushButton,
                           QListWidget, QListWidgetItem, QComboBox,
                           QColorDialog, QMessageBox, QFileDialog,
                           QMessageBox)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

from src.models.course import Course
from src.models.student import Student
from src.views.dialogs.import_csv_students_dialog import ImportCsvStudentsDialog
from src.views.dialogs.import_students_dialog import ImportStudentsDialog
from src.views.dialogs.grading_system_dialog import GradingSystemDialog

class CourseDialog(QDialog):
    def __init__(self, parent=None, course=None):
        super().__init__(parent)
        self.parent = parent
        self.course = course
        self.db = parent.parent.db
        self.selected_student_ids = []
        self.color = QColor('#FFFFFF')
        
        self.setWindowTitle("Kurs bearbeiten" if course else "Kurs hinzufügen")
        self.setMinimumWidth(600)
        self.setup_ui()

        if course:
            self.load_course_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Basis Informationen
        # Name
        layout.addWidget(QLabel("Name:*"))
        self.name = QLineEdit()
        layout.addWidget(self.name)

        # Typ
        layout.addWidget(QLabel("Typ:*"))
        self.type = QComboBox()
        self.type.addItems(["Klasse", "Kurs"])
        layout.addWidget(self.type)

        # Fach
        layout.addWidget(QLabel("Fach:"))
        self.subject = QComboBox()
        self.subject.setEditable(False)  # Änderung: keine freie Eingabe mehr
        self.load_subjects()  # Neue Methode
        self.subject.currentTextChanged.connect(self.on_subject_changed)
        layout.addWidget(self.subject)

        # Beschreibung
        layout.addWidget(QLabel("Beschreibung:"))
        self.description = QLineEdit()
        layout.addWidget(self.description)

        # Farbe
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Farbe:"))
        self.color_button = QPushButton()
        self.color_button.setFixedSize(40, 20)
        self.update_color_button()
        self.color_button.clicked.connect(self.choose_color)
        color_layout.addWidget(self.color_button)
        color_layout.addStretch()
        layout.addLayout(color_layout)

        # Bewertungssystem
        assessment_layout = QVBoxLayout()
        assessment_layout.addWidget(QLabel("Bewertungssystem:"))
        
        # Template-Auswahl und Bearbeiten-Button
        template_layout = QHBoxLayout()
        self.template = QComboBox()
        self.load_templates()  # Initial laden
        template_layout.addWidget(self.template)
        
        self.edit_types_btn = QPushButton("Bewertungstypen bearbeiten")
        self.edit_types_btn.setEnabled(False)  # Initial deaktiviert
        self.edit_types_btn.clicked.connect(self.edit_assessment_types)
        template_layout.addWidget(self.edit_types_btn)
        
        assessment_layout.addLayout(template_layout)
        layout.addLayout(assessment_layout)

        # Schüler Import
        import_layout = QHBoxLayout()
        
        import_csv_btn = QPushButton("Schüler aus CSV importieren")
        import_csv_btn.clicked.connect(self.import_from_csv)
        import_layout.addWidget(import_csv_btn)
        
        import_existing_btn = QPushButton("Schüler aus anderen Kursen importieren")
        import_existing_btn.clicked.connect(self.import_existing_students)
        import_layout.addWidget(import_existing_btn)
        
        layout.addLayout(import_layout)

        # Importierte Schüler anzeigen
        layout.addWidget(QLabel("Ausgewählte Schüler:"))
        self.student_list = QListWidget()
        self.student_list.setMaximumHeight(150)
        layout.addWidget(self.student_list)

        # Buttons
        button_box = QDialogButtonBox()
        
        if not self.course:  # Nur beim Erstellen
            save_new_btn = QPushButton("Speichern && Neu")
            save_new_btn.clicked.connect(self.save_and_new)
            button_box.addButton(save_new_btn, QDialogButtonBox.ButtonRole.ActionRole)

        button_box.addButton(QDialogButtonBox.StandardButton.Ok)
        button_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Pflichtfeld Hinweis
        layout.addWidget(QLabel("* Pflichtfeld"))

    def load_course_data(self):
        """Lädt die Daten eines existierenden Kurses"""
        self.name.setText(self.course.name)
        self.type.setCurrentText("Klasse" if self.course.type == 'class' else "Kurs")
        
        if self.course.subject:
            idx = self.subject.findText(self.course.subject)
            if idx >= 0:
                self.subject.setCurrentIndex(idx)
            else:
                self.subject.addItem(self.course.subject)
                self.subject.setCurrentText(self.course.subject)
                
        self.description.setText(self.course.description or "")
        
        if self.course.color:
            self.color = QColor(self.course.color)
            self.update_color_button()

        # Lade template_id und setze im ComboBox
        if self.course.template_id:
            # Lade Templates für das aktuelle Fach
            self.load_templates()
            # Setze die template_id im ComboBox
            idx = self.template.findData(self.course.template_id)
            if idx >= 0:
                self.template.setCurrentIndex(idx)

        # Aktiviere Bearbeiten-Button
        self.edit_types_btn.setEnabled(True)

        # Lade aktuelle Schüler
        self.load_current_students()

    def load_current_students(self):
        """Lädt die aktuellen Schüler des Kurses in die Liste"""
        try:
            # Hole aktuelles Semester
            semester = self.db.get_semester_dates()
            if not semester:
                return
                
            # Hole semester_id aus der Historie
            current_semester = self.db.get_semester_by_date(semester['semester_start'])
            if not current_semester:
                return
                
            # Hole Schüler
            students = self.db.get_students_by_course(self.course.id, current_semester['id'])
            
            # Aktualisiere Liste
            self.student_list.clear()
            for student in students:
                item = QListWidgetItem(f"{student['last_name']}, {student['first_name']}")
                item.setData(Qt.ItemDataRole.UserRole, student['id'])
                self.student_list.addItem(item)
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", 
                               f"Fehler beim Laden der Schüler: {str(e)}")

    def on_subject_changed(self, subject):
        """Handler für Änderungen am Fach"""
        self.load_templates()

    def load_templates(self):
        """Lädt die verfügbaren Bewertungsvorlagen für das aktuelle Fach"""
        try:
            self.template.clear()
            self.template.addItem("Keine Vorlage", None)
            
            subject = self.subject.currentText()
            if subject:
                templates = self.db.get_templates_by_subject(subject)
                for template in templates:
                    self.template.addItem(template['name'], template['id'])
                    
        except Exception as e:
            QMessageBox.critical(self, "Fehler", 
                               f"Fehler beim Laden der Vorlagen: {str(e)}")

    def update_color_button(self):
        """Aktualisiert die Farbe des Buttons"""
        self.color_button.setStyleSheet(
            f"background-color: {self.color.name()}; border: 1px solid gray;"
        )

    def choose_color(self):
        """Öffnet den Farbwähler-Dialog"""
        color = QColorDialog.getColor(self.color, self)
        if color.isValid():
            self.color = color
            self.update_color_button()

    def import_from_csv(self):
        """Importiert Schüler aus einer CSV-Datei"""
        if not self.course:
            QMessageBox.warning(self, "Fehler", "Bitte speichern Sie den Kurs zuerst")
            return
            
        filepath, _ = QFileDialog.getOpenFileName(
            self, "CSV-Datei auswählen", "", "CSV Dateien (*.csv)")
            
        if filepath:
            dialog = ImportCsvStudentsDialog(self, self.db)
            dialog.load_csv_data(filepath)
            if dialog.exec():
                self.load_current_students()
                QMessageBox.information(self, "Erfolg", 
                                      "Die Schüler wurden erfolgreich importiert")

    def import_existing_students(self):
        """Öffnet den Dialog zum Importieren existierender Schüler"""
        try:
            dialog = ImportStudentsDialog(self.parent.parent)
            if dialog.exec():
                self.selected_student_ids = dialog.get_selected_students()
                self.update_student_list()
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", 
                               f"Fehler beim Importieren der Schüler: {str(e)}")

    def update_student_list(self):
        """Aktualisiert die Anzeige der ausgewählten Schüler"""
        try:
            self.student_list.clear()
            for student_id in self.selected_student_ids:
                student = Student.get_by_id(self.db, student_id)
                if student:
                    item = QListWidgetItem(f"{student.last_name}, {student.first_name}")
                    item.setData(Qt.ItemDataRole.UserRole, student_id)
                    self.student_list.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", 
                               f"Fehler beim Aktualisieren der Liste: {str(e)}")

    def edit_assessment_types(self):
        """Öffnet den Dialog zum Bearbeiten der Bewertungstypen"""
        if not self.course:
            QMessageBox.warning(self, "Fehler", 
                              "Bitte speichern Sie den Kurs zuerst")
            return
            
        dialog = GradingSystemDialog(self, course_id=self.course.id)
        dialog.exec()

    def accept(self):
        """Validiert die Eingaben und speichert den Kurs"""
        try:
            # Validierung
            name = self.name.text().strip()
            if not name:
                QMessageBox.warning(self, "Fehler", "Bitte geben Sie einen Namen ein")
                self.name.setFocus()
                return

            window = self.parent.parent
            data = self.get_data()
            course_id = None
            template_id = data['template_id']
            template_changed = False
            
            if self.course:
                # Update
                # Prüfe ob template_id sich geändert hat
                old_template_id = self.course.template_id
                template_changed = (old_template_id != template_id)
                
                self.course.name = data['name']
                self.course.type = data['type']
                self.course.subject = data['subject']
                self.course.description = data['description']
                self.course.color = data['color']
                self.course.template_id = template_id
                self.course.update(window.db)
                course_id = self.course.id
                
                # Nur wenn template_id sich geändert hat
                if template_changed:
                    if template_id:
                        # Neue template_id gesetzt: Lösche alte Typen und erstelle neue
                        try:
                            # Lösche alte Bewertungstypen wenn template_id geändert wurde
                            existing_types = window.db.get_assessment_types(course_id)
                            if existing_types:
                                # Lösche alle bestehenden Typen
                                for atype in existing_types:
                                    window.db.delete_assessment_type(atype['id'])
                            
                            # Erstelle neue Bewertungstypen aus Template
                            window.db.create_assessment_types_from_template(course_id, template_id)
                            # Öffne direkt den Dialog zum Bearbeiten der Bewertungstypen
                            if QMessageBox.question(
                                self,
                                "Bewertungstypen",
                                "Möchten Sie jetzt die Bewertungstypen für diesen Kurs bearbeiten?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                            ) == QMessageBox.StandardButton.Yes:
                                from src.views.dialogs.grading_system_dialog import GradingSystemDialog
                                edit_dialog = GradingSystemDialog(self, course_id=course_id)
                                edit_dialog.exec()
                        except ValueError as e:
                            QMessageBox.information(self, "Hinweis", str(e))
                    else:
                        # template_id wurde entfernt (auf None gesetzt): Lösche alle Typen
                        existing_types = window.db.get_assessment_types(course_id)
                        if existing_types:
                            for atype in existing_types:
                                window.db.delete_assessment_type(atype['id'])
            else:
                # Neu
                course = Course.create(window.db, **data)
                course_id = course.id
                self.course = course
                
                # Nach Kurserstellung: Nur wenn template_id gesetzt wurde
                if template_id:
                    try:
                        # Course.create() hat bereits create_assessment_types_from_template aufgerufen
                        # Frage nur ob der Benutzer die Typen bearbeiten möchte
                        if QMessageBox.question(
                            self,
                            "Bewertungstypen",
                            "Möchten Sie jetzt die Bewertungstypen für diesen Kurs bearbeiten?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                        ) == QMessageBox.StandardButton.Yes:
                            from src.views.dialogs.grading_system_dialog import GradingSystemDialog
                            edit_dialog = GradingSystemDialog(self, course_id=course_id)
                            edit_dialog.exec()
                    except ValueError as e:
                        QMessageBox.information(self, "Hinweis", str(e))

            # Button aktivieren
            self.edit_types_btn.setEnabled(True)

            # Schüler verarbeiten
            semester_dates = window.db.get_semester_dates()
            if self.selected_student_ids and semester_dates:
                current_semester = window.db.get_semester_by_date(
                    semester_dates['semester_start'])
                    
                if current_semester:
                    for student_id in self.selected_student_ids:
                        student = Student.get_by_id(window.db, student_id)
                        if student:
                            student.add_course(window.db, course_id, 
                                            current_semester['id'])

            # Aktualisiere die UI des Hauptfensters
            if hasattr(self.parent, 'refresh_courses'):
                self.parent.refresh_courses()

            super().accept()  # Schließe den Dialog

        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def save_and_new(self):
        """Speichert den aktuellen Kurs und öffnet einen neuen Dialog"""
        self.accept()
        dialog = CourseDialog(self.parent)
        dialog.exec()

    def get_data(self):
        """Gibt die eingegebenen Daten zurück"""
        return {
            'name': self.name.text().strip(),
            'type': 'class' if self.type.currentText() == "Klasse" else 'course',
            'subject': self.subject.currentText().strip() or None,
            'description': self.description.text().strip() or None,
            'color': self.color.name(),
            'template_id': self.template.currentData()
        }

    def load_subjects(self):
        """Lädt die verfügbaren Fächer aus der Datenbank"""
        try:
            self.subject.clear()
            self.subject.addItem("", None)  # Leere Auswahl
            
            # Hole alle Fächer
            cursor = self.db.execute(
                "SELECT name FROM subjects ORDER BY name"
            )
            subjects = cursor.fetchall()
            
            for subject in subjects:
                self.subject.addItem(subject['name'])
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", 
                            f"Fehler beim Laden der Fächer: {str(e)}")

    def reload_subjects(self):
        """Aktualisiert die Fächerauswahl"""
        current = self.subject.currentText()
        self.load_subjects()
        # Versuche die vorherige Auswahl wiederherzustellen
        index = self.subject.findText(current)
        if index >= 0:
            self.subject.setCurrentIndex(index)