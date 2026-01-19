# src/database/db_manager.py

import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta  # timedelta hier hinzugefügt

# Repository-Imports
from .repositories import (
    StudentRepository,
    CourseRepository,
    LessonRepository,
    CompetencyRepository,
    AssessmentRepository,
    AssessmentTypeRepository,
    AssessmentTemplateRepository,
    GradingSystemRepository,
    SemesterRepository,
    HolidayRepository,
    AttendanceRepository,
    SettingsRepository,
)

class DatabaseManager:
    def __init__(self, db_file: str = "school.db"):
        self.db_file = db_file
        self.conn = None
        self.connect()
        self.setup_tables()
        
        # Repositories initialisieren
        self._init_repositories()
    
    def _init_repositories(self):
        """Initialisiert alle Repository-Instanzen."""
        self.students = StudentRepository(self)
        self.courses = CourseRepository(self)
        self.lessons = LessonRepository(self)
        self.competencies = CompetencyRepository(self)
        self.assessments = AssessmentRepository(self)
        self.assessment_types = AssessmentTypeRepository(self)
        self.assessment_templates = AssessmentTemplateRepository(self)
        self.grading_systems = GradingSystemRepository(self)
        self.semesters = SemesterRepository(self)
        self.holidays = HolidayRepository(self)
        self.attendance = AttendanceRepository(self)
        self.settings = SettingsRepository(self)
    
    def connect(self) -> None:
        """Stellt eine Verbindung zur Datenbank her."""
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.conn.row_factory = sqlite3.Row
            
            # Foreign Keys aktivieren und Status prüfen
            cursor = self.execute("PRAGMA foreign_keys = ON")
            cursor = self.execute("PRAGMA foreign_keys")
            fk_enabled = cursor.fetchone()[0]
            
        except sqlite3.Error as e:
            raise Exception(f"Datenbankverbindung fehlgeschlagen: {e}")

    def setup_tables(self) -> None:
        """Erstellt alle notwendigen Tabellen falls sie nicht existieren."""
        try:
            cursor = self.conn.cursor()
            
            # Studenten Tabelle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Kompetenzen Tabelle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS competencies (
                    id INTEGER PRIMARY KEY,
                    subject TEXT NOT NULL,
                    area TEXT NOT NULL,
                    description TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
        ''')
            
            # Einstellungen Tabelle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY,
                    semester_start TEXT,
                    semester_end TEXT
                )
            ''')

            # Erweiterte Noten-Tabelle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS grades (
                    id INTEGER PRIMARY KEY,
                    student_id INTEGER NOT NULL,
                    lesson_id INTEGER NOT NULL,
                    competency_id INTEGER NOT NULL,
                    grade INTEGER NOT NULL,
                    grade_type TEXT NOT NULL DEFAULT 'regular',
                    weight REAL DEFAULT 1.0,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
                    FOREIGN KEY (lesson_id) REFERENCES lessons (id) ON DELETE CASCADE,
                    FOREIGN KEY (competency_id) REFERENCES competencies (id) ON DELETE CASCADE,
                    CHECK (grade >= 1 AND grade <= 6),
                    CHECK (weight > 0 AND weight <= 2),
                    CHECK (grade_type IN ('regular', 'exam', 'oral', 'homework', 'project'))
                )
            ''')
            
            # Verknüpfungstabelle für Stunden und Kompetenzen
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lesson_competencies (
                    lesson_id INTEGER,
                    competency_id INTEGER,
                    FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE,
                    FOREIGN KEY (competency_id) REFERENCES competencies(id) ON DELETE CASCADE,
                    PRIMARY KEY (lesson_id, competency_id)
                )
            ''')     

            # Kurse/Klassen Tabelle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS courses (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('class', 'course')),
                    subject TEXT,
                    description TEXT,
                    color TEXT,
                    template_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (subject) REFERENCES subjects(name),
                    FOREIGN KEY (template_id) REFERENCES assessment_type_templates(id) ON DELETE SET NULL
                )
            ''')
            
            # Optionale Schüler-Kurs Zuordnung
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS student_courses (
                    student_id INTEGER,
                    course_id INTEGER,
                    semester_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (student_id, course_id, semester_id),
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                    FOREIGN KEY (semester_id) REFERENCES semester_history(id) ON DELETE CASCADE
                )
            ''')
            
            # Neue Tabelle für Halbjahreshistorie
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS semester_history (
                    id INTEGER PRIMARY KEY,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    name TEXT,  -- Optional für benutzerdefinierten Namen
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT  -- Optional für Anmerkungen
                )
            ''')
            

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lessons (
                    id INTEGER PRIMARY KEY,
                    course_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    homework TEXT,    
                    recurring_hash TEXT,
                    lesson_number INTEGER,
                    duration INTEGER,
                    status TEXT CHECK(status IN ('normal', 'cancelled', 'moved', 'substituted')) DEFAULT 'normal',
                    status_note TEXT,
                    moved_to_lesson_id INTEGER REFERENCES lessons(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
                )
            ''')

            try:
                cursor.execute("ALTER TABLE lessons ADD COLUMN homework TEXT")
            except sqlite3.Error:
                # Ignoriere Fehler wenn Spalte bereits existiert
                pass

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS timetable_settings (
                    id INTEGER PRIMARY KEY,
                    first_lesson_start TEXT NOT NULL,  -- z.B. "08:00"
                    lesson_duration INTEGER NOT NULL,   -- in Minuten
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS breaks (
                    id INTEGER PRIMARY KEY,
                    after_lesson INTEGER NOT NULL,      -- nach welcher Stunde
                    duration INTEGER NOT NULL,          -- in Minuten
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Prüfe ob bereits Einstellungen vorhanden sind
            cursor.execute("SELECT COUNT(*) as count FROM timetable_settings")
            if cursor.fetchone()['count'] == 0:
                # Füge Standardeinstellungen ein
                cursor.execute(
                    """INSERT INTO timetable_settings 
                    (id, first_lesson_start, lesson_duration) 
                    VALUES (1, '08:00', 45)"""
                )
                
                # Füge Standardpausen ein
                standard_breaks = [
                    (1, 5),   # Nach 1. Stunde: 5 Minuten
                    (2, 15),  # Nach 2. Stunde: 15 Minuten
                    (3, 5),   # Nach 3. Stunde: 5 Minuten
                    (4, 20),  # Nach 4. Stunde: 20 Minuten
                    (5, 5),   # Nach 5. Stunde: 5 Minuten
                    (6, 10),  # Nach 6. Stunde: 10 Minuten
                    (7, 5),   # Nach 7. Stunde: 5 Minuten
                    (8, 5),   # Nach 8. Stunde: 5 Minuten
                    (9, 5),   # Nach 9. Stunde: 5 Minuten
                ]
                
                cursor.executemany(
                    "INSERT INTO breaks (after_lesson, duration) VALUES (?, ?)",
                    standard_breaks
                )

            # Bemerkungen Tabelle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS student_remarks (
                    id INTEGER PRIMARY KEY,
                    student_id INTEGER NOT NULL,
                    lesson_id INTEGER,  -- Optional
                    remark_text TEXT NOT NULL,
                    type TEXT DEFAULT 'general',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                    FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE SET NULL
                )
            ''')

            # Notensysteme (z.B. Unterstufe 1-6, Oberstufe 0-15)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS grading_systems (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    min_grade REAL NOT NULL,
                    max_grade REAL NOT NULL,
                    step_size REAL NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Beispiel-Notensysteme einfügen
            cursor.execute("SELECT COUNT(*) as count FROM grading_systems")
            if cursor.fetchone()['count'] == 0:
                cursor.execute('''
                    INSERT INTO grading_systems 
                    (name, min_grade, max_grade, step_size, description)
                    VALUES 
                    ('Unterstufe (1-6)', 1.0, 6.0, 0.33, 'Klassisches Notensystem mit + und -'),
                    ('Oberstufe (0-15)', 0.0, 15.0, 1.0, 'Punktesystem der gymnasialen Oberstufe')
                ''')

            # Vorlagen für Bewertungstypen
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS assessment_type_templates (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    description TEXT,
                    grading_system_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (grading_system_id) REFERENCES grading_systems(id)
                )
            ''')

            # Einzelne Bewertungstypen in Vorlagen
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS template_items (
                    id INTEGER PRIMARY KEY,
                    template_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    parent_item_id INTEGER,
                    default_weight REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (template_id) REFERENCES assessment_type_templates(id) ON DELETE CASCADE,
                    FOREIGN KEY (parent_item_id) REFERENCES template_items(id) ON DELETE CASCADE
                )
            ''')

            # Konkrete Bewertungstypen für Kurse
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS assessment_types (
                    id INTEGER PRIMARY KEY,
                    course_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    parent_type_id INTEGER,
                    weight REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                    FOREIGN KEY (parent_type_id) REFERENCES assessment_types(id) ON DELETE CASCADE
                )
            ''')

            # Konkrete Bewertungen/Noten
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS assessments (
                    id INTEGER PRIMARY KEY,
                    student_id INTEGER NOT NULL,
                    course_id INTEGER NOT NULL,
                    assessment_type_id INTEGER NOT NULL,
                    lesson_id INTEGER,
                    grade REAL NOT NULL,
                    weight REAL DEFAULT 1.0,
                    date TEXT NOT NULL,
                    topic TEXT,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                    FOREIGN KEY (assessment_type_id) REFERENCES assessment_types(id) ON DELETE CASCADE,
                    FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE SET NULL
                )
            ''')

            # Tabelle für Abwesenheiten
            cursor.execute('''    
                CREATE TABLE IF NOT EXISTS student_attendance (
                    id INTEGER PRIMARY KEY,
                    student_id INTEGER NOT NULL,
                    lesson_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                    FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE,
                    UNIQUE(student_id, lesson_id)
                )
            ''')

            # Tabelle für Fächer
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subjects (
                    name TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Feiertage und Ferientage (automatisch über API)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS public_holidays (
                    id INTEGER PRIMARY KEY,
                    date TEXT NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT CHECK(type IN ('holiday', 'vacation_day')) NOT NULL,
                    state TEXT NOT NULL,  -- Bundesland 
                    year INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Zusätzliche schulspezifische freie Tage (manuell)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS school_holidays (
                    id INTEGER PRIMARY KEY,
                    date TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # # Prüfe ob die template_id Spalte existiert, wenn nicht füge sie hinzu
            # try:
            #     cursor.execute("ALTER TABLE courses ADD COLUMN template_id INTEGER REFERENCES assessment_type_templates(id)")
            # except sqlite3.OperationalError as e:
            #     if "duplicate column name" not in str(e).lower():
            #         raise e

            self.conn.commit()               
        except sqlite3.Error as e:
            raise Exception(f"Fehler beim Erstellen der Tabellen: {e}")                 

            # Indizes für bessere Performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_grades_student ON grades(student_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_grades_lesson ON grades(lesson_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_grades_competency ON grades(competency_id)')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_remarks_student 
            ON student_remarks(student_id)
        ''')
        

    # DEPRECATED: Legacy-Methoden für Kompatibilität mit Models
    # Diese werden nur noch von Models verwendet und sollten langfristig entfernt werden.

    # Kompetenz-bezogene Methoden wurden entfernt - nutze self.competencies.* stattdessen

    # Noten-bezogene Methoden
    # def add_grade(self, student_id: int, lesson_id: int, 
    #              competency_id: int, grade: int, comment: str = "") -> int:
    #     """Fügt eine neue Note hinzu."""
    #     cursor = self.execute(
    #         """INSERT INTO grades 
    #            (student_id, lesson_id, competency_id, grade, comment)
    #            VALUES (?, ?, ?, ?, ?)""",
    #         (student_id, lesson_id, competency_id, grade, comment)
    #     )
    #     return cursor.lastrowid

    # def get_grades_by_student(self, student_id: int) -> List[Dict[str, Any]]:
    #     """Holt alle Noten eines Schülers mit zugehörigen Informationen."""
    #     cursor = self.execute(
    #         """SELECT g.*, l.subject, l.date, c.area, c.description
    #            FROM grades g
    #            JOIN lessons l ON g.lesson_id = l.id
    #            JOIN competencies c ON g.competency_id = c.id
    #            WHERE g.student_id = ?
    #            ORDER BY l.date DESC""",
    #         (student_id,)
    #     )
    #     return [dict(row) for row in cursor.fetchall()]

    # Semester-Methoden (behalten für Kompatibilität mit Models und Views)
    def get_semester_dates(self) -> dict:
        """Holt die aktuellen Semesterdaten.
        
        DEPRECATED: Verwende self.semesters.get_current() stattdessen.
        Wird noch in Models und Views als Fallback verwendet.
        """
        return self.semesters.get_current()
    
    def get_semester_by_date(self, date: str) -> dict:
        """Findet das Halbjahr zu einem bestimmten Datum.
        
        DEPRECATED: Verwende self.semesters.get_by_date() stattdessen.
        Wird noch in Models verwendet.
        """
        result = self.semesters.get_by_date(date)
        return result if result else None

    # Hilfsmethode für Datenbankoperationen
    def execute(self, query: str, params: tuple = None):
        """Führt eine SQL-Query aus und handled Fehler."""
        try:
            cursor = self.conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.conn.commit()
            return cursor
        except sqlite3.Error as e:
            self.conn.rollback()
            raise Exception(f"Datenbankfehler: {e}")

    def __del__(self):
        """Schließt die Datenbankverbindung beim Beenden."""
        if self.conn:
            self.conn.close()

    # def add_grade(self, data: dict) -> int:
    #     """Fügt eine neue Note hinzu mit erweiterten Eigenschaften."""
    #     try:
    #         cursor = self.execute('''
    #             INSERT INTO grades (
    #                 student_id, lesson_id, competency_id, 
    #                 grade, grade_type, weight, comment
    #             ) VALUES (?, ?, ?, ?, ?, ?, ?)
    #         ''', (
    #             data['student_id'], 
    #             data['lesson_id'],
    #             data['competency_id'],
    #             data['grade'],
    #             data.get('grade_type', 'regular'),
    #             data.get('weight', 1.0),
    #             data.get('comment', '')
    #         ))
    #         return cursor.lastrowid
    #     except sqlite3.Error as e:
    #         raise Exception(f"Fehler beim Hinzufügen der Note: {e}")

    # Lesson-Methoden (behalten für Kompatibilität)
    def get_lesson(self, lesson_id: int) -> dict:
        """Holt eine einzelne Unterrichtsstunde.
        
        DEPRECATED: Verwende self.lessons.get_by_id() stattdessen.
        Wird noch in Views als Fallback verwendet.
        """
        result = self.lessons.get_by_id(lesson_id)
        return result if result else None

    # Course-Methoden (behalten für Kompatibilität)
    def get_all_courses(self) -> list:
        """Holt alle verfügbaren Kurse und Klassen.
        
        DEPRECATED: Verwende self.courses.get_all() stattdessen.
        Wird noch in Views als Fallback verwendet.
        """
        return self.courses.get_all()


    # Notensystem-Methoden (entfernt - nutze self.grading_systems.* stattdessen)
    # validate_grade wird aus Kompatibilitätsgründen weiterhin bereitgestellt
    def validate_grade(self, grade: float, system_id: int) -> bool:
        """Prüft ob eine Note in einem Notensystem gültig ist.
        
        DEPRECATED: Verwende self.grading_systems.validate_grade() stattdessen.
        Wird noch intern verwendet (in validate_assessment_input).
        """
        return self.grading_systems.validate_grade(grade, system_id)

# Assessment-Template-Methoden (entfernt - nutze self.assessment_templates.* stattdessen)


# Attendance-Methoden (entfernt - nutze self.attendance.* stattdessen)


# Holiday-Methoden (behalten für Kompatibilität)
    def update_lesson_status_for_holidays(self):
        """Aktualisiert den Status von Stunden, die in Ferien/an Feiertagen liegen.
        
        DEPRECATED: Verwende self.holidays.update_lesson_status_for_holidays() stattdessen.
        Wird noch in Models verwendet (HolidayManager).
        """
        self.holidays.update_lesson_status_for_holidays()