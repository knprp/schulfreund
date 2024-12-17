from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QDialogButtonBox)

class StudentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Schüler hinzufügen")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Name Eingabefeld
        name_layout = QVBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name = QLineEdit()
        name_layout.addWidget(self.name)
        layout.addLayout(name_layout)

        # OK und Abbrechen Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)