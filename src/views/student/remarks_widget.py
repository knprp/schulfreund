# src/views/student/remarks_widget.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                           QTableWidgetItem, QHeaderView, QPushButton, QMessageBox)
from src.models.student.remarks import StudentRemark

class RemarksWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent.main_window
        self.current_student_id = None
        self.setup_ui()

    def setup_ui(self):
        """Erstellt die UI-Komponenten"""
        layout = QVBoxLayout(self)

        # Tabelle für Bemerkungen
        self.remarks_table = QTableWidget()
        self.remarks_table.setColumnCount(3)
        self.remarks_table.setHorizontalHeaderLabels(["Datum", "Typ", "Bemerkung"])
        self.remarks_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.remarks_table)

        # Buttons für Bemerkungen
        button_layout = QHBoxLayout()
        
        add_remark_btn = QPushButton("Bemerkung hinzufügen")
        add_remark_btn.clicked.connect(self.add_remark)
        button_layout.addWidget(add_remark_btn)
        
        delete_remark_btn = QPushButton("Bemerkung löschen")
        delete_remark_btn.clicked.connect(self.delete_remark)
        button_layout.addWidget(delete_remark_btn)
        
        layout.addLayout(button_layout)

    def load_remarks(self, student_id: int):
        """Lädt die Bemerkungen eines Schülers"""
        try:
            self.current_student_id = student_id
            remarks = StudentRemark.get_for_student(self.main_window.db, student_id)
            
            self.remarks_table.setRowCount(len(remarks))
            for row, remark in enumerate(remarks):
                self.remarks_table.setItem(
                    row, 0,
                    QTableWidgetItem(remark.created_at)
                )
                self.remarks_table.setItem(
                    row, 1,
                    QTableWidgetItem(remark.type)
                )
                self.remarks_table.setItem(
                    row, 2,
                    QTableWidgetItem(remark.remark_text)
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Laden der Bemerkungen: {str(e)}"
            )

    def add_remark(self):
        """Öffnet den Dialog zum Hinzufügen einer Bemerkung"""
        try:
            if not self.current_student_id:
                return
                
            from src.views.dialogs.remark_dialog import RemarkDialog
            dialog = RemarkDialog(self.main_window)
            
            if dialog.exec():
                data = dialog.get_data()
                # Der Dialog gibt vermutlich 'remark_text' statt 'text' zurück
                StudentRemark.create(
                    self.main_window.db,
                    self.current_student_id,
                    remark_text=data['remark_text'],  # Hier war der Fehler
                    type=data['type']
                )
                self.load_remarks(self.current_student_id)
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Hinzufügen der Bemerkung: {str(e)}"
            )

    def delete_remark(self):
        """Löscht die ausgewählte Bemerkung"""
        try:
            selected = self.remarks_table.selectedItems()
            if not selected:
                return
                
            row = selected[0].row()
            date = self.remarks_table.item(row, 0).text()
            text = self.remarks_table.item(row, 2).text()
            
            reply = QMessageBox.question(
                self,
                'Bemerkung löschen',
                f'Möchten Sie die Bemerkung vom {date} wirklich löschen?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Suche die Bemerkung anhand des Datums
                remarks = StudentRemark.get_for_student(self.main_window.db, self.current_student_id)
                for remark in remarks:
                    if remark.created_at == date and remark.remark_text == text:
                        remark.delete(self.main_window.db)
                        break
                        
                self.load_remarks(self.current_student_id)
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Löschen der Bemerkung: {str(e)}"
            )