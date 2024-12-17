# src/views/tabs/course_tab.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QTableWidget, QTableWidgetItem, QHeaderView, 
                           QMessageBox, QMenu)
from PyQt6.QtCore import Qt
from src.views.dialogs.course_dialog import CourseDialog
from src.models.course import Course

class CourseTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        self.refresh_courses()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tabelle für Kurse
        self.courses_table = QTableWidget()
        self.courses_table.setColumnCount(4)
        self.courses_table.setHorizontalHeaderLabels(['Name', 'Typ', 'Fach', 'Beschreibung'])
        self.courses_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.courses_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.courses_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        btn_add = QPushButton("Kurs hinzufügen")
        btn_add.clicked.connect(self.add_course)
        button_layout.addWidget(btn_add)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Kontext-Menü für die Tabelle
        self.courses_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.courses_table.customContextMenuRequested.connect(self.show_context_menu)

    def add_course(self):
        try:
            dialog = CourseDialog(self)
            if dialog.exec():
                data = dialog.get_data()
                Course.create(self.parent.db, **data)
                self.refresh_courses()
                self.parent.statusBar().showMessage(f"Kurs {data['name']} wurde hinzugefügt", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def edit_course(self, course_id):
        try:
            course = Course.get_by_id(self.parent.db, course_id)
            if course:
                dialog = CourseDialog(self, course)
                if dialog.exec():
                    data = dialog.get_data()
                    course.name = data['name']
                    course.type = data['type']
                    course.subject = data['subject']
                    course.description = data['description']
                    course.update(self.parent.db)
                    self.refresh_courses()
                    self.parent.statusBar().showMessage(f"Kurs {data['name']} wurde aktualisiert", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def delete_course(self, course_id):
        try:
            course = Course.get_by_id(self.parent.db, course_id)
            if course:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Question)
                msg.setText(f"Möchten Sie den Kurs '{course.name}' wirklich löschen?")
                msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                
                if msg.exec() == QMessageBox.StandardButton.Yes:
                    course.delete(self.parent.db)
                    self.refresh_courses()
                    self.parent.statusBar().showMessage(f"Kurs {course.name} wurde gelöscht", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def show_context_menu(self, pos):
        item = self.courses_table.itemAt(pos)
        if item is None:
            return
            
        menu = QMenu()
        edit_action = menu.addAction("Bearbeiten")
        delete_action = menu.addAction("Löschen")
        
        action = menu.exec(self.courses_table.viewport().mapToGlobal(pos))
        if not action:
            return
            
        row = self.courses_table.row(item)
        course_id = self.courses_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        if action == edit_action:
            self.edit_course(course_id)
        elif action == delete_action:
            self.delete_course(course_id)

    def refresh_courses(self):
        try:
            self.courses_table.setRowCount(0)
            courses = Course.get_all(self.parent.db)
            
            for course in courses:
                row = self.courses_table.rowCount()
                self.courses_table.insertRow(row)
                
                # Name
                item = QTableWidgetItem(course.name)
                item.setData(Qt.ItemDataRole.UserRole, course.id)
                self.courses_table.setItem(row, 0, item)
                
                # Typ
                type_text = "Klasse" if course.type == 'class' else "Kurs"
                self.courses_table.setItem(row, 1, QTableWidgetItem(type_text))
                
                # Fach
                self.courses_table.setItem(row, 2, QTableWidgetItem(course.subject or ""))
                
                # Beschreibung
                self.courses_table.setItem(row, 3, QTableWidgetItem(course.description or ""))
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Kurse: {str(e)}")