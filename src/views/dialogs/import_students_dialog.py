from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                           QTreeView, QListView, QLabel, QDialogButtonBox)
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt

class ImportStudentsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Schüler importieren")
        self.resize(800, 500)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        inner_layout = QHBoxLayout()
        
        # Linke Seite (Baumansicht)
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Verfügbare Schüler:"))
        
        self.tree_view = QTreeView()
        self.tree_model = QStandardItemModel()
        self.tree_model.setHorizontalHeaderLabels(["Name"])
        self.tree_view.setModel(self.tree_model)
        self.tree_view.setSelectionMode(QTreeView.SelectionMode.ExtendedSelection)
        left_layout.addWidget(self.tree_view)
        inner_layout.addLayout(left_layout)
        
        # Mittlere Buttons
        middle_layout = QVBoxLayout()
        self.add_button = QPushButton(">>")
        self.add_button.clicked.connect(self.add_selected)
        self.remove_button = QPushButton("<<")
        self.remove_button.clicked.connect(self.remove_selected)
        middle_layout.addStretch()
        middle_layout.addWidget(self.add_button)
        middle_layout.addWidget(self.remove_button)
        middle_layout.addStretch()
        inner_layout.addLayout(middle_layout)
        
        # Rechte Seite (ausgewählte Schüler)
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Ausgewählte Schüler:"))
        
        self.list_view = QListView()
        self.list_model = QStandardItemModel()
        self.list_view.setModel(self.list_model)
        self.list_view.setSelectionMode(QListView.SelectionMode.ExtendedSelection)
        right_layout.addWidget(self.list_view)
        inner_layout.addLayout(right_layout)
        
        main_layout.addLayout(inner_layout)
        
        # Dialog-Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
        
        self.setLayout(main_layout)

    def load_data(self):
        """Lädt die Halbjahres-/Kurs-/Schülerstruktur"""
        try:
            # Hole alle Halbjahre
            semesters = self.parent.controllers.semester.get_semester_history()
            print(f"Gefundene Halbjahre: {semesters}")  # DEBUG
            
            for semester in semesters:
                semester_name = semester['name'] or f"{semester['start_date']} - {semester['end_date']}"
                semester_item = QStandardItem(semester_name)
                semester_item.setData(semester['id'], Qt.ItemDataRole.UserRole)
                semester_item.setData('semester', Qt.ItemDataRole.UserRole + 1)
                
                # Hole Kurse für dieses Halbjahr
                courses = self.parent.controllers.course.get_courses_by_semester(semester['id'])
                print(f"Gefundene Kurse für {semester_name}: {courses}")  # DEBUG
                
                for course in courses:
                    course_name = f"{course['name']} ({course['student_count']} Schüler)"
                    course_item = QStandardItem(course_name)
                    course_item.setData(course['id'], Qt.ItemDataRole.UserRole)
                    course_item.setData('course', Qt.ItemDataRole.UserRole + 1)
                    
                    # Hole Schüler für diesen Kurs
                    students = self.parent.controllers.course.get_students_by_course(course['id'], semester['id'])
                    print(f"Gefundene Schüler für {course_name}: {students}")  # DEBUG
                    
                    for student in students:
                        student_name = f"{student['last_name']}, {student['first_name']}"
                        student_item = QStandardItem(student_name)
                        student_item.setData(student['id'], Qt.ItemDataRole.UserRole)
                        student_item.setData('student', Qt.ItemDataRole.UserRole + 1)
                        course_item.appendRow(student_item)
                    
                    semester_item.appendRow(course_item)
                
                self.tree_model.appendRow(semester_item)
                
            # Expandiere alle Halbjahre
            for row in range(self.tree_model.rowCount()):
                self.tree_view.expand(self.tree_model.index(row, 0))
                
        except Exception as e:
            print(f"Fehler beim Laden der Daten: {e}")

    def add_selected(self):
        """Fügt ausgewählte Schüler zur rechten Liste hinzu"""
        selected = self.tree_view.selectedIndexes()
        for index in selected:
            item = self.tree_model.itemFromIndex(index)
            if item.data(Qt.ItemDataRole.UserRole + 1) == 'student':  # Nur Schüler
                # Prüfe ob Schüler bereits in der Liste ist
                found = False
                for row in range(self.list_model.rowCount()):
                    if (self.list_model.item(row).data(Qt.ItemDataRole.UserRole) == 
                        item.data(Qt.ItemDataRole.UserRole)):
                        found = True
                        break
                
                if not found:
                    new_item = QStandardItem(item.text())
                    new_item.setData(item.data(Qt.ItemDataRole.UserRole), 
                                   Qt.ItemDataRole.UserRole)
                    self.list_model.appendRow(new_item)

    def remove_selected(self):
        """Entfernt ausgewählte Schüler aus der rechten Liste"""
        selected = self.list_view.selectedIndexes()
        for index in reversed(selected):  # Reverse, damit Indizes stimmen bleiben
            self.list_model.removeRow(index.row())

    def get_selected_students(self):
        """Gibt die IDs der ausgewählten Schüler zurück"""
        student_ids = []
        for row in range(self.list_model.rowCount()):
            item = self.list_model.item(row)
            student_ids.append(item.data(Qt.ItemDataRole.UserRole))
        return student_ids