from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QTableWidget, QTableWidgetItem, QMessageBox, QMenu,
                           QGroupBox, QHeaderView)
from PyQt6.QtCore import Qt
from datetime import datetime
from src.views.dialogs.student_dialog import StudentDialog
from src.models.student import Student
from src.views.dialogs.remark_dialog import RemarkDialog

class StudentTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_student = None  # ID des aktuell ausgewählten Schülers
        self.setup_ui()
        self.refresh_students()

        self.students_table.itemSelectionChanged.connect(self.on_student_selected)

    def setup_ui(self):
        """Erstellt das UI des Schüler-Tabs"""
        # Hauptlayout als HBox für zwei Spalten
        main_layout = QHBoxLayout(self)
        
        # Linke Spalte für Schülerliste
        left_column = QVBoxLayout()
        
        # Tabelle für Schüler
        self.students_table = QTableWidget()
        self.students_table.setColumnCount(2)  # Vorname und Nachname
        self.students_table.setHorizontalHeaderLabels(['Nachname', 'Vorname'])
        self.students_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.students_table.verticalHeader().setVisible(False)
        # Nur Zeilenauswahl erlauben
        self.students_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.students_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        # Beide Spalten sollen sich strecken
        header = self.students_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        left_column.addWidget(self.students_table)
        
        # Button zum Hinzufügen
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Schüler hinzufügen")
        btn_add.clicked.connect(self.add_student)
        btn_layout.addWidget(btn_add)
        btn_layout.addStretch()
        left_column.addLayout(btn_layout)
        
        # Kontextmenü einrichten
        self.students_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.students_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Rechte Spalte für Bemerkungen
        right_column = QVBoxLayout()
        
        # GroupBox für Bemerkungen
        remarks_group = QGroupBox("Bemerkungen")
        remarks_layout = QVBoxLayout()
        
        # Tabelle für Bemerkungen
        self.remarks_table = QTableWidget()
        self.remarks_table.setColumnCount(3)
        self.remarks_table.setHorizontalHeaderLabels(["Datum", "Typ", "Text"])
        self.remarks_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        remarks_layout.addWidget(self.remarks_table)
        
        # Button für neue Bemerkung
        btn_add_remark = QPushButton("Neue Bemerkung")
        btn_add_remark.clicked.connect(self.add_remark)
        remarks_layout.addWidget(btn_add_remark)
        
        remarks_group.setLayout(remarks_layout)
        right_column.addWidget(remarks_group)
        
        # Spalten zum Hauptlayout hinzufügen
        main_layout.addLayout(left_column)
        main_layout.addLayout(right_column)

    def add_student(self):
        """Fügt einen neuen Schüler hinzu"""
        try:
            while True:
                dialog = StudentDialog(self)
                result = dialog.exec()
                
                if result == 0:  # Abbrechen wurde geklickt
                    break
                    
                data = dialog.get_data()
                student = Student.create(self.parent.db, **data)
                self.refresh_students()
                self.parent.statusBar().showMessage(
                    f"Schüler {student.get_full_name()} wurde hinzugefügt", 3000)
                
                if result == 1:  # OK wurde geklickt
                    break
                # Bei result == 2 ("Speichern & Neu") geht die Schleife weiter
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def refresh_students(self):
        """Aktualisiert die Schülerliste"""
        try:
            self.students_table.setRowCount(0)
            students = Student.get_all(self.parent.db)
            
            for student in students:
                row = self.students_table.rowCount()
                self.students_table.insertRow(row)
                
                # Nachname
                last_name_item = QTableWidgetItem(student.last_name)
                last_name_item.setData(Qt.ItemDataRole.UserRole, student.id)
                self.students_table.setItem(row, 0, last_name_item)
                
                # Vorname
                first_name_item = QTableWidgetItem(student.first_name)
                self.students_table.setItem(row, 1, first_name_item)
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Schüler: {str(e)}")

    def edit_student(self, student_id):
        """Bearbeitet einen existierenden Schüler"""
        try:
            student = Student.get_by_id(self.parent.db, student_id)
            if student:
                dialog = StudentDialog(self, student)
                if dialog.exec():
                    data = dialog.get_data()
                    student.first_name = data['first_name']
                    student.last_name = data['last_name']
                    student.update(self.parent.db)
                    self.refresh_students()
                    self.parent.statusBar().showMessage(
                        f"Schüler wurde zu {student.get_full_name()} umbenannt", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def delete_student(self, student_id):
        """Löscht einen Schüler"""
        try:
            student = Student.get_by_id(self.parent.db, student_id)
            if student:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Question)
                msg.setText(f"Möchten Sie den Schüler '{student.get_full_name()}' wirklich löschen?")
                msg.setStandardButtons(
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                
                if msg.exec() == QMessageBox.StandardButton.Yes:
                    student.delete(self.parent.db)
                    self.refresh_students()
                    self.parent.statusBar().showMessage(
                        f"Schüler {student.get_full_name()} wurde gelöscht", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def show_context_menu(self, pos):
        """Zeigt das Kontextmenü für die Schülertabelle"""
        
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

    def on_student_selected(self):
        """Handler für Schülerauswahl"""
        items = self.students_table.selectedItems()
        if not items:
            self.current_student = None
            return
            
        item = items[0]
        self.current_student = item.data(Qt.ItemDataRole.UserRole)  # ID aus UserRole holen
        self.load_remarks(self.current_student)  # Lade Bemerkungen

    def select_student(self, student_id):
        """Wählt einen bestimmten Schüler aus."""
        for row in range(self.students_table.rowCount()):
            if int(self.students_table.item(row, 0).text()) == student_id:
                self.students_table.selectRow(row)
                break


    def setup_remarks_ui(self):
        """Richtet die UI-Komponenten für Bemerkungen ein."""
        # Gruppierung für Bemerkungen
        remarks_group = QGroupBox("Bemerkungen")
        remarks_layout = QVBoxLayout()

        # Liste für Bemerkungen
        self.remarks_table = QTableWidget()
        self.remarks_table.setColumnCount(3)
        self.remarks_table.setHorizontalHeaderLabels(["Datum", "Typ", "Text"])
        self.remarks_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        remarks_layout.addWidget(self.remarks_table)

        # Button zum Hinzufügen
        add_button = QPushButton("Neue Bemerkung")
        add_button.clicked.connect(self.add_remark)
        remarks_layout.addWidget(add_button)

        remarks_group.setLayout(remarks_layout)
        self.right_layout.addWidget(remarks_group)  # Füge zur rechten Spalte hinzu

        # Kontextmenü für Bemerkungen
        self.remarks_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.remarks_table.customContextMenuRequested.connect(self.show_remarks_context_menu)

    def load_remarks(self, student_id: int):
        """Lädt die Bemerkungen eines Schülers."""
        try:
            student = Student.get_by_id(self.parent.db, student_id)
            if not student:
                return
                
            remarks = student.get_remarks(self.parent.db)
            self.remarks_table.setRowCount(len(remarks))
            
            for row, remark in enumerate(remarks):
                # Datum
                date_item = QTableWidgetItem(
                    datetime.strptime(remark.created_at, "%Y-%m-%d %H:%M:%S")
                    .strftime("%d.%m.%Y %H:%M")
                )
                self.remarks_table.setItem(row, 0, date_item)
                
                # Typ
                type_mapping = {
                    'general': 'Allgemein',
                    'behavior': 'Verhalten',
                    'achievement': 'Leistung',
                    'attendance': 'Anwesenheit'
                }
                type_item = QTableWidgetItem(type_mapping.get(remark.type, 'Allgemein'))
                self.remarks_table.setItem(row, 1, type_item)
                
                # Text
                text_item = QTableWidgetItem(remark.remark_text)
                self.remarks_table.setItem(row, 2, text_item)
                
                # Speichere remark.id für spätere Verwendung
                date_item.setData(Qt.ItemDataRole.UserRole, remark.id)
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Bemerkungen: {str(e)}")

    def add_remark(self):
        """Fügt eine neue Bemerkung hinzu."""
        if not self.current_student:
            QMessageBox.warning(self, "Warnung", "Bitte wählen Sie zuerst einen Schüler aus.")
            return
            
        try:
            dialog = RemarkDialog(self)
            if dialog.exec():
                data = dialog.get_data()
                student = Student.get_by_id(self.parent.db, self.current_student)
                student.add_remark(
                    self.parent.db,
                    text=data['remark_text'],
                    type=data['type']
                )
                self.load_remarks(self.current_student)
                self.parent.statusBar().showMessage("Bemerkung wurde hinzugefügt", 3000)
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Hinzufügen der Bemerkung: {str(e)}")

    def show_remarks_context_menu(self, pos):
        """Zeigt das Kontextmenü für Bemerkungen."""
        item = self.remarks_table.itemAt(pos)
        if not item:
            return
            
        menu = QMenu()
        edit_action = menu.addAction("Bearbeiten")
        delete_action = menu.addAction("Löschen")
        
        action = menu.exec(self.remarks_table.viewport().mapToGlobal(pos))
        if not action:
            return
            
        row = self.remarks_table.row(item)
        remark_id = self.remarks_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        if action == edit_action:
            self.edit_remark(remark_id)
        elif action == delete_action:
            self.delete_remark(remark_id)

    def edit_remark(self, remark_id: int):
        """Bearbeitet eine existierende Bemerkung."""
        try:
            remark = StudentRemark.get_by_id(self.parent.db, remark_id)
            if not remark:
                return
                
            dialog = RemarkDialog(self, remark)
            if dialog.exec():
                data = dialog.get_data()
                remark.remark_text = data['remark_text']
                remark.type = data['type']
                remark.update(self.parent.db)
                
                self.load_remarks(self.current_student)
                self.parent.statusBar().showMessage("Bemerkung wurde aktualisiert", 3000)
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Bearbeiten der Bemerkung: {str(e)}")

    def delete_remark(self, remark_id: int):
        """Löscht eine Bemerkung."""
        try:
            remark = StudentRemark.get_by_id(self.parent.db, remark_id)
            if not remark:
                return
                
            reply = QMessageBox.question(
                self,
                'Bemerkung löschen',
                'Möchten Sie diese Bemerkung wirklich löschen?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                remark.delete(self.parent.db)
                self.load_remarks(self.current_student)
                self.parent.statusBar().showMessage("Bemerkung wurde gelöscht", 3000)
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Löschen der Bemerkung: {str(e)}")