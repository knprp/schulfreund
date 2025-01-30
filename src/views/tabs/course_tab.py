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
        
        # Kontextmenü
        self.courses_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.courses_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Rechte Seite - Details
        self.detail_tabs = QTabWidget()
        
        # Tab für Stunden
        self.lessons_widget = QTableWidget()
        self.lessons_widget.setColumnCount(4)
        self.lessons_widget.setHorizontalHeaderLabels(['Datum', 'Zeit', 'Thema', 'Kompetenzen'])
        # Konfiguration für Stunden-Table
        self.lessons_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.lessons_widget.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.lessons_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        # Doppelklick aktivieren
        self.lessons_widget.itemDoubleClicked.connect(self.on_lesson_double_clicked)
        
        self.detail_tabs.addTab(self.lessons_widget, "Stunden")
        
        # Tab für Noten
        self.grades_widget = QTableWidget()
        self.grades_widget.setColumnCount(5)
        self.grades_widget.setHorizontalHeaderLabels(['Datum', 'Name', 'Kompetenzen', 'Art', 'Durchschnitt'])
        self.grades_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.grades_widget.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.grades_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.grades_widget.itemDoubleClicked.connect(self.on_grade_double_clicked)
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
            # Hole alle Stunden mit ihren Kompetenzen
            cursor = self.parent.db.execute("""
                SELECT DISTINCT 
                    l.id,
                    l.date,
                    l.time,
                    l.topic,
                    l.duration,
                    GROUP_CONCAT(c.area || ': ' || c.description) as competencies
                FROM lessons l
                LEFT JOIN lesson_competencies lc ON l.id = lc.lesson_id
                LEFT JOIN competencies c ON lc.competency_id = c.id
                WHERE l.course_id = ?
                GROUP BY l.id
                ORDER BY l.date DESC, l.time DESC
            """, (course_id,))
            
            lessons = cursor.fetchall()
            
            # Tabelle leeren und Größe anpassen
            self.lessons_widget.setRowCount(0)
            self.lessons_widget.setRowCount(len(lessons))
            
            
            # Spaltenbreiten optimieren
            header = self.lessons_widget.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Datum
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Zeit
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)          # Thema
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)          # Kompetenzen
            
            for row, lesson in enumerate(lessons):
                # Datum
                date_item = QTableWidgetItem(lesson['date'])
                self.lessons_widget.setItem(row, 0, date_item)
                
                # Zeit (mit Doppelstunden-Markierung)
                time_text = lesson['time']
                if lesson['duration'] == 2:
                    time_text += " (Doppelstunde)"
                time_item = QTableWidgetItem(time_text)
                self.lessons_widget.setItem(row, 1, time_item)
                
                # Thema
                topic_item = QTableWidgetItem(lesson['topic'] or "")
                self.lessons_widget.setItem(row, 2, topic_item)
                
                # Kompetenzen
                comp_text = lesson['competencies'] or ""
                comp_item = QTableWidgetItem(comp_text.replace(",", "\n"))
                self.lessons_widget.setItem(row, 3, comp_item)
                
                # Lesson-ID als Userdata speichern
                date_item.setData(Qt.ItemDataRole.UserRole, lesson['id'])
                
            # Automatische Auswahl der nächsten Stunde
            if self.lessons_widget.rowCount() > 0:
                # Aktuelle Zeit/Datum für Vergleich
                current_date = QDate.currentDate().toString("yyyy-MM-dd")
                current_time = QTime.currentTime().toString("HH:mm")
                
                # Suche zuerst nach Stunden am aktuellen Tag
                current_day_rows = []
                future_rows = []
                past_rows = []
                
                for row in range(self.lessons_widget.rowCount()):
                    lesson_date = self.lessons_widget.item(row, 0).text()
                    lesson_time = self.lessons_widget.item(row, 1).text().split(" ")[0]  # Zeit ohne "(Doppelstunde)"
                    
                    if lesson_date == current_date:
                        current_day_rows.append((row, lesson_time))
                    elif lesson_date > current_date:
                        future_rows.append((row, lesson_date))
                    else:
                        past_rows.append((row, lesson_date))
                
                # Finde die nächste Stunde für heute
                next_row = None
                if current_day_rows:
                    # Sortiere nach Zeit
                    current_day_rows.sort(key=lambda x: x[1])
                    # Finde die nächste Stunde heute
                    for row, time in current_day_rows:
                        if time >= current_time:
                            next_row = row
                            break
                    # Wenn keine spätere Stunde heute, nehme die erste Stunde des nächsten Datums
                    if next_row is None and future_rows:
                        future_rows.sort(key=lambda x: x[1])  # Sortiere nach Datum
                        next_row = future_rows[0][0]
                # Wenn kein heutiges Datum gefunden, nimm das nächste verfügbare Datum
                elif future_rows:
                    future_rows.sort(key=lambda x: x[1])  # Sortiere nach Datum
                    next_row = future_rows[0][0]
                # Wenn keine zukünftigen Stunden, nimm die letzte vergangene Stunde
                elif past_rows:
                    past_rows.sort(key=lambda x: x[1], reverse=True)  # Sortiere nach Datum absteigend
                    next_row = past_rows[0][0]
                else:
                    next_row = 0  # Fallback auf erste Zeile
                
                # Zeile auswählen und sichtbar machen
                self.lessons_widget.selectRow(next_row)
                self.lessons_widget.scrollTo(
                    self.lessons_widget.model().index(next_row, 0),
                    QAbstractItemView.ScrollHint.PositionAtCenter
                )

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
            lesson_id = self.lessons_widget.item(item.row(), 0).data(Qt.ItemDataRole.UserRole)
            
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

    def load_course_grades(self, course_id: int):
        """Lädt alle Bewertungen des ausgewählten Kurses"""
        try:
            # Hole alle Bewertungen mit zugehörigen Details
            cursor = self.parent.db.execute("""
                SELECT 
                    a.date,
                    s.first_name || ' ' || s.last_name as student_name,
                    GROUP_CONCAT(c.area || ': ' || c.description) as competencies,
                    at.name as assessment_type,
                    ROUND(AVG(a.grade), 2) as average_grade,
                    a.topic,
                    COUNT(DISTINCT s.id) as student_count,
                    a.lesson_id
                FROM assessments a
                JOIN students s ON a.student_id = s.id
                JOIN assessment_types at ON a.assessment_type_id = at.id
                LEFT JOIN lessons l ON a.lesson_id = l.id
                LEFT JOIN lesson_competencies lc ON l.id = lc.lesson_id
                LEFT JOIN competencies c ON lc.competency_id = c.id
                WHERE a.course_id = ?
                GROUP BY a.date, a.topic, at.id
                ORDER BY a.date DESC, at.name
            """, (course_id,))
            
            grades = cursor.fetchall()
            
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
            course = Course.get_by_id(self.parent.db, course_id)
            if course:
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