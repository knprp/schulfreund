# src/views/tabs/course_tab.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QTableWidget, QTableWidgetItem, QHeaderView, 
                           QMessageBox, QMenu, QSplitter, QTabWidget,
                           QAbstractItemView)
from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from src.views.dialogs.course_dialog import CourseDialog
from src.views.dialogs.lesson_details_dialog import LessonDetailsDialog
from src.models.course import Course
from src.views.delegates.strikeout_delegate import StrikeoutDelegate    

class CourseTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        self.refresh_courses()

    def setup_ui(self):
        # Hauptlayout ist jetzt horizontal
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Splitter für flexible Größenanpassung
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Linke Seite - Kursübersicht
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(8, 8, 8, 8)
        
        # Kurstabelle
        self.courses_table = QTableWidget()
        self.courses_table.setColumnCount(4)
        self.courses_table.setHorizontalHeaderLabels(['Name', 'Typ', 'Fach', 'Beschreibung'])
        self.courses_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.courses_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.courses_table.itemSelectionChanged.connect(self.on_course_selected)
        
        # Styling der Tabelle
        font = self.courses_table.font()
        font.setPointSize(11)
        self.courses_table.setFont(font)
        
        header_font = self.courses_table.horizontalHeader().font()
        header_font.setPointSize(11)
        header_font.setBold(True)
        self.courses_table.horizontalHeader().setFont(header_font)
        
        self.courses_table.verticalHeader().setDefaultSectionSize(40)
        self.courses_table.setShowGrid(True)
        self.courses_table.setAlternatingRowColors(False)
        self.courses_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
                font-size: 11pt;
            }
            QHeaderView::section {
                padding: 8px;
                font-size: 11pt;
                background-color: #f0f0f0;
            }
        """)
        
        left_layout.addWidget(self.courses_table)
        
        # Button zum Hinzufügen
        button_layout = QHBoxLayout()
        btn_add = QPushButton("Kurs hinzufügen")
        btn_add.setMinimumHeight(32)
        btn_add.setFont(font)
        btn_add.clicked.connect(self.add_course)
        button_layout.addWidget(btn_add)
        button_layout.addStretch()
        left_layout.addLayout(button_layout)
        
        # Kontextmenü Kurse
        self.courses_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.courses_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Rechte Seite - Details
        self.detail_tabs = QTabWidget()
        
        # Tab für Stunden
        self.lesson_table = QTableWidget()
        self.lesson_table.setColumnCount(4)
        self.lesson_table.setHorizontalHeaderLabels(['Datum', 'Zeit', 'Thema', 'Kompetenzen'])
        # Konfiguration für Stunden-Table
        self.lesson_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.lesson_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.lesson_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        # Doppelklick aktivieren
        self.lesson_table.itemDoubleClicked.connect(self.on_lesson_double_clicked)
        
        self.detail_tabs.addTab(self.lesson_table, "Stunden")

        self.lesson_table.setItemDelegate(StrikeoutDelegate(self.lesson_table, self.parent.db, self.parent))
        
        # Tab für Noten
        self.grades_widget = QTableWidget()
        self.grades_widget.setColumnCount(5)
        self.grades_widget.setHorizontalHeaderLabels(['Datum', 'Name', 'Kompetenzen', 'Art', 'Durchschnitt'])
        self.grades_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.grades_widget.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.grades_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.grades_widget.itemDoubleClicked.connect(self.on_grade_double_clicked)
        self.detail_tabs.addTab(self.grades_widget, "Noten")
        
        # Kontextmenü Noten
        self.grades_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.grades_widget.customContextMenuRequested.connect(self.show_grades_context_menu)
        self.detail_tabs.addTab(self.grades_widget, "Noten")
        
        # Widgets zum Splitter hinzufügen
        splitter.addWidget(left_widget)
        splitter.addWidget(self.detail_tabs)
        
        # Initiale Größenverhältnisse setzen (40% links, 60% rechts)
        splitter.setSizes([400, 600])
        
        # Splitter zum Hauptlayout hinzufügen
        main_layout.addWidget(splitter)

    def on_course_selected(self):
        """Handler für Kursauswahl - lädt die Details des ausgewählten Kurses"""
        selected_items = self.courses_table.selectedItems()
        if not selected_items:
            return
            
        course_id = self.courses_table.item(selected_items[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        self.load_course_details(course_id)

    def load_course_details(self, course_id: int):
        """Lädt die Details (Stunden und Noten) für den ausgewählten Kurs"""
        self.load_course_lessons(course_id)
        self.load_course_grades(course_id)

    def load_course_lessons(self, course_id: int):
        """Lädt die Stunden des ausgewählten Kurses"""
        try:
            # Lade Stunden über Controller
            lessons = self.parent.controllers.course.get_course_lessons(course_id)
            
            # Tabelle leeren und Größe anpassen
            self.lesson_table.setRowCount(0)
            self.lesson_table.setColumnCount(5)  # Jetzt 5 Spalten
            self.lesson_table.setHorizontalHeaderLabels(['Datum', 'Zeit', 'Thema', 'Kompetenzen', 'Status'])
            
            # Spaltenbreiten optimieren
            header = self.lesson_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Datum
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Zeit
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)           # Thema
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)           # Kompetenzen
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Status
            
            self.lesson_table.setRowCount(len(lessons))
            
            # Stunden einfügen (lessons ist jetzt eine Liste von Dictionaries)
            for row, lesson in enumerate(lessons):
                # Datum
                date_item = QTableWidgetItem(lesson['date'])
                self.lesson_table.setItem(row, 0, date_item)
                
                # Zeit (mit Doppelstunden-Markierung)
                time_text = lesson['time']
                if lesson['duration'] == 2:
                    time_text += " (Doppelstunde)"
                time_item = QTableWidgetItem(time_text)
                self.lesson_table.setItem(row, 1, time_item)
                
                # Thema
                topic_item = QTableWidgetItem(lesson['topic'] or "")
                self.lesson_table.setItem(row, 2, topic_item)
                
                # Kompetenzen
                comp_text = lesson['competencies'] or ""
                comp_item = QTableWidgetItem(comp_text.replace(",", "\n"))
                self.lesson_table.setItem(row, 3, comp_item)
                
                # Status mit Note (neu)
                status = lesson['status'] if lesson['status'] is not None else 'normal'
                status_text = {
                    'normal': 'Normal',
                    'cancelled': 'Entfällt',
                    'moved': 'Verlegt',
                    'substituted': 'Vertretung'
                }.get(status, status)

                if lesson['status_note'] is not None:
                    status_text += f"\n{lesson['status_note']}"
                    
                status_item = QTableWidgetItem(status_text)

                # Farbliche Markierung je nach Status
                if status == 'cancelled':
                    status_item.setBackground(QColor(255, 200, 200))  # Hellrot
                elif status == 'moved':
                    status_item.setBackground(QColor(255, 255, 200))  # Hellgelb
                elif status == 'substituted':
                    status_item.setBackground(QColor(200, 255, 200))  # Hellgrün
                    
                self.lesson_table.setItem(row, 4, status_item)
                
                # Lesson-ID als Userdata speichern
                date_item.setData(Qt.ItemDataRole.UserRole, lesson['id'])
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler", 
                f"Fehler beim Laden der Stunden: {str(e)}"
            )

    def on_lesson_double_clicked(self, item):
        """Öffnet den LessonDetailsDialog für die ausgewählte Stunde"""
        try:
            # Hole die lesson_id aus der ersten Spalte der ausgewählten Zeile
            lesson_id = self.lesson_table.item(item.row(), 0).data(Qt.ItemDataRole.UserRole)
            
            dialog = LessonDetailsDialog(self.parent, lesson_id)
            if dialog.exec():
                # Nach Schließen des Dialogs Stundenliste aktualisieren
                selected_items = self.courses_table.selectedItems()
                if selected_items:
                    course_id = self.courses_table.item(selected_items[0].row(), 0).data(Qt.ItemDataRole.UserRole)
                    self.load_course_lessons(course_id)
                    
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Fehler", 
                f"Fehler beim Öffnen der Stundendetails: {str(e)}"
            )

    def on_grade_double_clicked(self, item):
        """Öffnet den LessonDetailsDialog für die ausgewählte Note"""
        try:
            # Hole die lesson_id aus der ersten Spalte der ausgewählten Zeile
            lesson_id = self.grades_widget.item(item.row(), 0).data(Qt.ItemDataRole.UserRole)
            if lesson_id:  # Nur öffnen wenn es eine verknüpfte Stunde gibt
                dialog = LessonDetailsDialog(self.parent, lesson_id)
                # Setze den Tab auf "Schüler" (Index 1)
                dialog.tab_widget.setCurrentIndex(1)
                if dialog.exec():
                    # Nach Schließen des Dialogs Notenliste aktualisieren
                    selected_items = self.courses_table.selectedItems()
                    if selected_items:
                        course_id = self.courses_table.item(selected_items[0].row(), 0).data(Qt.ItemDataRole.UserRole)
                        self.load_course_grades(course_id)
                        
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Fehler", 
                f"Fehler beim Öffnen der Stundendetails: {str(e)}"
            )
                
    def show_grades_context_menu(self, pos):
        """Zeigt das Kontextmenü für die Noten"""
        item = self.grades_widget.itemAt(pos)
        if item is None:
            return
            
        row = item.row()
        lesson_id = self.grades_widget.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not lesson_id:
            return
            
        menu = QMenu()
        delete_action = menu.addAction("Bewertung löschen")
        
        action = menu.exec(self.grades_widget.viewport().mapToGlobal(pos))
        if action == delete_action:
            self.delete_grade_group(row)
                

    def load_course_grades(self, course_id: int):
        """Lädt alle Bewertungen des ausgewählten Kurses"""
        try:
            # Hole alle Bewertungen mit zugehörigen Details über Controller
            grades = self.parent.controllers.course.get_course_grades_detailed(course_id)
            
            # Tabelle leeren und Größe anpassen
            self.grades_widget.setRowCount(0)
            self.grades_widget.setRowCount(len(grades))
            
            # Spaltenbreiten optimieren
            header = self.grades_widget.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Datum
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Name
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)          # Kompetenzen
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Art
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Durchschnitt
            
            # Bewertungen einfügen
            for row, grade in enumerate(grades):
                # Datum
                date_item = QTableWidgetItem(grade['date'])
                if grade['lesson_id']:
                    date_item.setData(Qt.ItemDataRole.UserRole, grade['lesson_id'])
                self.grades_widget.setItem(row, 0, date_item)
                
                # Name für die Bewertung (z.B. "Klassenarbeit 1" oder der erste Schülername)
                name = grade['topic'] if grade['topic'] else grade['student_name']
                if grade['student_count'] > 1:
                    name += f" (+{grade['student_count']-1} weitere)"
                name_item = QTableWidgetItem(name)
                self.grades_widget.setItem(row, 1, name_item)
                
                # Kompetenzen
                comp_text = grade['competencies'] or ""
                comp_item = QTableWidgetItem(comp_text.replace(",", "\n"))
                self.grades_widget.setItem(row, 2, comp_item)
                
                # Art der Bewertung
                type_item = QTableWidgetItem(grade['assessment_type'])
                self.grades_widget.setItem(row, 3, type_item)
                
                # Durchschnittsnote
                avg_item = QTableWidgetItem(f"{grade['average_grade']:.2f}")
                # Rechts ausrichten
                avg_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.grades_widget.setItem(row, 4, avg_item)
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Laden der Bewertungen: {str(e)}"
            )

    def delete_grade_group(self, row):
        """Löscht alle Noten der ausgewählten Bewertung"""
        try:
            lesson_id = self.grades_widget.item(row, 0).data(Qt.ItemDataRole.UserRole)
            display_name = self.grades_widget.item(row, 1).text()
            
            print(f"DEBUG: Versuche Noten zu löschen für lesson_id={lesson_id}")
            
            # Bestätigung einholen
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText(f"Möchten Sie wirklich alle Noten für '{display_name}' löschen?")
            msg.setInformativeText("Diese Aktion kann nicht rückgängig gemacht werden.")
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg.setDefaultButton(QMessageBox.StandardButton.No)
            
            if msg.exec() == QMessageBox.StandardButton.Yes:
                # Lösche alle Noten dieser Stunde über Controller
                deleted_count = self.parent.controllers.assessment.delete_assessments_by_lesson(lesson_id)
                print(f"DEBUG: {deleted_count} Noten wurden gelöscht")

                # Aktualisiere die Ansicht
                selected_items = self.courses_table.selectedItems()
                if selected_items:
                    course_id = self.courses_table.item(selected_items[0].row(), 0).data(Qt.ItemDataRole.UserRole)
                    print(f"DEBUG: Aktualisiere Ansicht für Kurs {course_id}")
                    self.load_course_grades(course_id)
                    
                self.parent.statusBar().showMessage(f"{count} Bewertungen wurden gelöscht", 3000)
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Fehler", 
                f"Fehler beim Löschen der Bewertung: {str(e)}"
            )

    def add_course(self):
        try:
            dialog = CourseDialog(self)
            if dialog.exec():
                # Die Kurserstellung erfolgt jetzt im Dialog, 
                # wir müssen nur noch die Liste aktualisieren
                self.refresh_courses()
                self.parent.statusBar().showMessage("Kurs wurde hinzugefügt", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def edit_course(self, course_id):
        try:
            # Lade Kurs über Controller
            course_data = self.parent.controllers.course.get_course(course_id)
            if course_data:
                # Konvertiere Dictionary in Course-Objekt für Kompatibilität
                course = Course(
                    id=course_data['id'],
                    name=course_data['name'],
                    type=course_data.get('type', 'course'),
                    subject=course_data.get('subject'),
                    description=course_data.get('description'),
                    color=course_data.get('color')
                )
                dialog = CourseDialog(self, course)
                if dialog.exec():
                    data = dialog.get_data()
                    course.name = data['name']
                    course.type = data['type']
                    course.subject = data['subject']
                    course.description = data['description']
                    course.color = data['color']
                    course.update(self.parent.db)
                    self.refresh_courses()
                    self.parent.statusBar().showMessage(f"Kurs {data['name']} wurde aktualisiert", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def delete_course(self, course_id):
        try:
            # Lade Kurs über Controller, um Namen zu holen
            course_data = self.parent.controllers.course.get_course(course_id)
            if course_data:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Question)
                msg.setText(f"Möchten Sie den Kurs '{course_data['name']}' wirklich löschen?")
                msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                
                if msg.exec() == QMessageBox.StandardButton.Yes:
                    # Lösche Kurs über Controller
                    self.parent.controllers.course.delete_course(course_id)
                    self.refresh_courses()
                    self.parent.statusBar().showMessage(f"Kurs {course_data['name']} wurde gelöscht", 3000)
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
            # Lade Kurse über Controller
            courses_data = self.parent.controllers.course.get_all_courses()
            # Konvertiere Dictionaries in Course-Objekte für Kompatibilität
            from src.models.course import Course
            courses = []
            for course_data in courses_data:
                course = Course(
                    id=course_data['id'],
                    name=course_data['name'],
                    type=course_data.get('type', 'course'),
                    subject=course_data.get('subject'),
                    description=course_data.get('description'),
                    color=course_data.get('color')
                )
                courses.append(course)
            for course in courses:
                row = self.courses_table.rowCount()
                self.courses_table.insertRow(row)
                
                # Farbhandling
                background_color = None
                if course.color:
                    color = QColor(course.color)
                    color.setAlpha(40)  # 15% Deckkraft
                    background_color = color

                # Name
                item = QTableWidgetItem(course.name)
                item.setData(Qt.ItemDataRole.UserRole, course.id)
                if background_color:
                    item.setBackground(background_color)
                self.courses_table.setItem(row, 0, item)
                
                # Typ
                item = QTableWidgetItem("Klasse" if course.type == 'class' else "Kurs")
                if background_color:
                    item.setBackground(background_color)
                self.courses_table.setItem(row, 1, item)
                
                # Fach
                item = QTableWidgetItem(course.subject or "")
                if background_color:
                    item.setBackground(background_color)
                self.courses_table.setItem(row, 2, item)
                
                # Beschreibung
                item = QTableWidgetItem(course.description or "")
                if background_color:
                    item.setBackground(background_color)
                self.courses_table.setItem(row, 3, item)
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Kurse: {str(e)}")