from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QTableWidget, QTableWidgetItem, QMessageBox)
from PyQt6.QtCore import Qt
from src.views.dialogs.student_dialog import StudentDialog
from src.models.student import Student

class StudentTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        self.refresh_students()

    def setup_ui(self):
        """Erstellt das UI des Schüler-Tabs"""
        layout = QVBoxLayout(self)
        
        # Tabelle für Schüler
        self.students_table = QTableWidget()
        self.students_table.setColumnCount(1)
        self.students_table.setHorizontalHeaderLabels(['Name'])
        self.students_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.students_table.verticalHeader().setVisible(False)
        self.students_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.students_table)
        
        # Button zum Hinzufügen
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Schüler hinzufügen")
        btn_add.clicked.connect(self.add_student)
        btn_layout.addWidget(btn_add)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Kontextmenü einrichten
        self.students_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.students_table.customContextMenuRequested.connect(self.show_context_menu)

    def add_student(self):
        """Fügt einen neuen Schüler hinzu"""
        try:
            dialog = StudentDialog(self)
            if dialog.exec():
                name = dialog.name.text().strip()
                if not name:
                    raise ValueError("Der Name darf nicht leer sein")
                    
                student = Student.create(self.parent.db, name)
                self.refresh_students()
                self.parent.statusBar().showMessage(f"Schüler {name} wurde hinzugefügt", 3000)
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def refresh_students(self):
        """Aktualisiert die Schülertabelle"""
        try:
            self.students_table.setRowCount(0)
            students = Student.get_all(self.parent.db)
            for student in students:
                row = self.students_table.rowCount()
                self.students_table.insertRow(row)
                item = QTableWidgetItem(student.name)
                item.setData(Qt.ItemDataRole.UserRole, student.id)
                self.students_table.setItem(row, 0, item)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def show_context_menu(self, pos):
        """Zeigt das Kontextmenü für die Schülertabelle"""
        from PyQt6.QtWidgets import QMenu
        
        item = self.students_table.itemAt(pos)
        if item is None:
            return
            
        menu = QMenu()
        edit_action = menu.addAction("Bearbeiten")
        delete_action = menu.addAction("Löschen")
        
        action = menu.exec(self.students_table.viewport().mapToGlobal(pos))
        if not action:
            return
            
        row = self.students_table.row(item)
        student_id = self.students_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        if action == edit_action:
            self.edit_student(student_id)
        elif action == delete_action:
            self.delete_student(student_id)

    def edit_student(self, student_id):
        """Bearbeitet einen existierenden Schüler"""
        try:
            student = Student.get_by_id(self.parent.db, student_id)
            if student:
                dialog = StudentDialog(self)
                dialog.name.setText(student.name)
                if dialog.exec():
                    new_name = dialog.name.text().strip()
                    if new_name:
                        student.name = new_name
                        student.update(self.parent.db)
                        self.refresh_students()
                        self.parent.statusBar().showMessage(
                            f"Schüler wurde zu {new_name} umbenannt", 3000)
                    else:
                        raise ValueError("Der Name darf nicht leer sein")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def delete_student(self, student_id):
        """Löscht einen Schüler"""
        try:
            student = Student.get_by_id(self.parent.db, student_id)
            if student:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Question)
                msg.setText(f"Möchten Sie den Schüler '{student.name}' wirklich löschen?")
                msg.setStandardButtons(
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                
                if msg.exec() == QMessageBox.StandardButton.Yes:
                    student.delete(self.parent.db)
                    self.refresh_students()
                    self.parent.statusBar().showMessage(
                        f"Schüler {student.name} wurde gelöscht", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))