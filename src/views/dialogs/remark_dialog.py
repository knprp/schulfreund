# src/views/dialogs/remark_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QComboBox, QDialogButtonBox,
                           QTextEdit)
from datetime import datetime

class RemarkDialog(QDialog):
    def __init__(self, parent=None, remark=None):
        super().__init__(parent)
        self.remark = remark
        self.setWindowTitle("Bemerkung hinzufügen" if not remark else "Bemerkung bearbeiten")
        self.setup_ui()
        
        if remark:
            self.load_remark_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Typ der Bemerkung
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Typ:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Allgemein", "Verhalten", "Leistung", "Anwesenheit"])
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)

        # Text der Bemerkung
        layout.addWidget(QLabel("Text:"))
        self.text_edit = QTextEdit()
        layout.addWidget(self.text_edit)

        # Dialog-Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_remark_data(self):
        """Lädt die Daten einer existierenden Bemerkung."""
        # Typ setzen
        type_mapping = {
            'general': 'Allgemein',
            'behavior': 'Verhalten',
            'achievement': 'Leistung',
            'attendance': 'Anwesenheit'
        }
        self.type_combo.setCurrentText(type_mapping.get(self.remark.type, 'Allgemein'))
        
        # Text setzen
        self.text_edit.setText(self.remark.remark_text)

    def get_data(self):
        """Gibt die eingegebenen Daten zurück."""
        # Typ-Mapping für die Datenbank
        type_mapping = {
            'Allgemein': 'general',
            'Verhalten': 'behavior',
            'Leistung': 'achievement',
            'Anwesenheit': 'attendance'
        }
        
        return {
            'type': type_mapping[self.type_combo.currentText()],
            'remark_text': self.text_edit.toPlainText().strip()
        }