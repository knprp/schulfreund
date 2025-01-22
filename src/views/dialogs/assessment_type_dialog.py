# src/views/dialogs/assessment_type_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                           QDoubleSpinBox, QDialogButtonBox)

class AssessmentTypeDialog(QDialog):
    def __init__(self, parent=None, template_id=None, parent_type_id=None):
        super().__init__(parent)
        self.template_id = template_id
        self.parent_type_id = parent_type_id
        self.setWindowTitle("Bewertungstyp hinzufügen")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Name:*"))
        self.name = QLineEdit()
        layout.addWidget(self.name)

        layout.addWidget(QLabel("Gewichtung:"))
        self.weight = QDoubleSpinBox()
        self.weight.setRange(0.1, 2.0)
        self.weight.setValue(1.0)
        self.weight.setSingleStep(0.1)
        layout.addWidget(self.weight)

        layout.addWidget(QLabel("* Pflichtfeld"))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self) -> dict:
        return {
            'name': self.name.text().strip(),
            'parent_item_id': self.parent_type_id,
            'default_weight': self.weight.value()
        }