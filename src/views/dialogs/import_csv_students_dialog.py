from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                          QLabel, QTableWidget, QTableWidgetItem, QGroupBox, 
                          QDialogButtonBox, QMessageBox)
from PyQt6.QtCore import Qt
import csv

class ImportCsvStudentsDialog(QDialog):
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.parent = parent
        self.db = db
        # Controller müssen verfügbar sein
        if hasattr(parent, 'parent') and hasattr(parent.parent, 'controllers'):
            self.main_window = parent.parent
        elif hasattr(parent, 'controllers'):
            self.main_window = parent
        else:
            raise ValueError("ImportCsvStudentsDialog benötigt Zugriff auf Controller.")
        self.course_id = parent.course.id
        self.setWindowTitle("Schüler aus CSV importieren")
        self.setMinimumWidth(800)
        self.setup_ui()


    def setup_ui(self):
       layout = QVBoxLayout(self)
       
       # Info-Label
       info = QLabel("CSV-Format: Nachname, Vorname in zwei Spalten oder durch Komma getrennt")
       layout.addWidget(info)

       # Vorschau-Tabelle
       self.preview_table = QTableWidget()
       self.preview_table.setColumnCount(4)
       self.preview_table.setHorizontalHeaderLabels([
           "Importieren", "Original", "Vorname", "Nachname"
       ])
       self.preview_table.horizontalHeader().setStretchLastSection(True)
       layout.addWidget(self.preview_table)

       # Buttons für Massenauswahl
       select_layout = QHBoxLayout()
       select_all = QPushButton("Alle auswählen")
       select_all.clicked.connect(lambda: self.set_all_checkboxes(Qt.CheckState.Checked))
       select_none = QPushButton("Keine auswählen")
       select_none.clicked.connect(lambda: self.set_all_checkboxes(Qt.CheckState.Unchecked))
       select_layout.addWidget(select_all)
       select_layout.addWidget(select_none)
       select_layout.addStretch()
       layout.addLayout(select_layout)

       # Dialog-Buttons
       button_box = QDialogButtonBox(
           QDialogButtonBox.StandardButton.Ok | 
           QDialogButtonBox.StandardButton.Cancel
       )
       button_box.accepted.connect(self.validate_and_accept)
       button_box.rejected.connect(self.reject)
       layout.addWidget(button_box)

    def load_csv_data(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)  # Header überspringen
                next(reader)  # Leere Zeile überspringen
                self.preview_table.setRowCount(0)
                for row in reader:
                    if not row:  # Prüfe ob die Zeile überhaupt Daten enthält
                        continue
                        
                    original = row[0].strip()
                    if not original:  
                        continue
                            
                    # Stoppe beim ersten alleinstehendem X
                    x_pos = original.find("X")
                    if x_pos >= 0 and (x_pos == 0 or original[x_pos-1].isspace()):
                        original = original[:x_pos].strip()
                        
                    row_pos = self.preview_table.rowCount()
                    self.preview_table.insertRow(row_pos)

                    # Checkbox
                    checkbox = QTableWidgetItem()
                    checkbox.setCheckState(Qt.CheckState.Checked)
                    self.preview_table.setItem(row_pos, 0, checkbox)

                    # Original Name
                    self.preview_table.setItem(row_pos, 1, QTableWidgetItem(original))

                    # Name aufteilen
                    if ',' in original:  # Komma-getrennt
                        parts = [p.strip() for p in original.split(',')]
                        self.preview_table.setItem(row_pos, 2, QTableWidgetItem(parts[1]))
                        self.preview_table.setItem(row_pos, 3, QTableWidgetItem(parts[0]))
                    else:  # Leerzeichen-getrennt
                        name_parts = original.split()
                        if len(name_parts) == 2:
                            self.preview_table.setItem(row_pos, 2, QTableWidgetItem(name_parts[1]))
                            self.preview_table.setItem(row_pos, 3, QTableWidgetItem(name_parts[0]))
                        elif len(name_parts) > 2:
                            self.preview_table.setItem(row_pos, 2, QTableWidgetItem(name_parts[-1]))
                            self.preview_table.setItem(row_pos, 3, QTableWidgetItem(" ".join(name_parts[:-1])))
                        else:
                            self.preview_table.setItem(row_pos, 2, QTableWidgetItem(""))
                            self.preview_table.setItem(row_pos, 3, QTableWidgetItem(original))

                self.preview_table.resizeColumnsToContents()

        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der CSV-Datei: {str(e)}")

    def set_all_checkboxes(self, state):
       for row in range(self.preview_table.rowCount()):
           self.preview_table.item(row, 0).setCheckState(state)

    def validate_and_accept(self):
        try:
            current_semester = self.main_window.controllers.semester.get_semester_dates()
            if not current_semester:
                raise ValueError("Kein aktives Semester gefunden")

            # Hole semester_id aus der Historie
            semester_data = self.main_window.controllers.semester.get_semester_by_date(
                current_semester['semester_start']
            )
            if not semester_data:
                raise ValueError("Aktives Semester nicht in der Historie gefunden")
            semester = {'id': semester_data['id']}

            students_to_import = []
            for row in range(self.preview_table.rowCount()):
                if self.preview_table.item(row, 0).checkState() == Qt.CheckState.Checked:
                    first_name = self.preview_table.item(row, 2).text().strip()
                    last_name = self.preview_table.item(row, 3).text().strip()

                    if not first_name or not last_name:
                        raise ValueError(f"Bitte füllen Sie Vor- und Nachname für Zeile {row + 1}")

                    students_to_import.append({
                        'first_name': first_name,
                        'last_name': last_name
                    })

            # Importiere Schüler und füge sie zum Kurs hinzu
            for student in students_to_import:
                student_id = self.main_window.controllers.student.create_student(
                    student['first_name'], student['last_name']
                )
                self.main_window.controllers.student.add_student_to_course(
                    student_id, self.course_id, semester['id']
                )

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))