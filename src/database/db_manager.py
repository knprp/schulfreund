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
        

    # Student-bezogene Methoden (delegieren an StudentRepository)
    def add_student(self, name: str = None, first_name: str = None, last_name: str = None) -> int:
        """Fügt einen neuen Schüler hinzu und gibt seine ID zurück.
        
        DEPRECATED: Verwende self.students.add() stattdessen.
        Unterstützt alte API (nur name) und neue API (first_name, last_name).
        """
        if name:
            # Alte API: name wird in first_name und last_name aufgeteilt
            parts = name.strip().split(' ', 1)
            first_name = parts[0] if parts else ""
            last_name = parts[1] if len(parts) > 1 else ""
        elif first_name is None or last_name is None:
            raise ValueError("Entweder 'name' oder 'first_name' und 'last_name' müssen angegeben werden")
        
        return self.students.add(first_name, last_name)

    def get_student(self, student_id: int) -> Optional[Dict[str, Any]]:
        """Holt einen einzelnen Schüler anhand seiner ID.
        
        DEPRECATED: Verwende self.students.get_by_id() stattdessen.
        """
        return self.students.get_by_id(student_id)

    def get_all_students(self) -> list:
        """Holt alle Schüler aus der Datenbank.
        
        DEPRECATED: Verwende self.students.get_all() stattdessen.
        """
        return self.students.get_all()

    def update_student(self, student_id: int, name: str = None, 
                      first_name: str = None, last_name: str = None) -> None:
        """Aktualisiert die Daten eines Schülers.
        
        DEPRECATED: Verwende self.students.update() stattdessen.
        Unterstützt alte API (nur name) und neue API (first_name, last_name).
        """
        if name:
            # Alte API: name wird in first_name und last_name aufgeteilt
            parts = name.strip().split(' ', 1)
            first_name = parts[0] if parts else ""
            last_name = parts[1] if len(parts) > 1 else ""
        elif first_name is None or last_name is None:
            raise ValueError("Entweder 'name' oder 'first_name' und 'last_name' müssen angegeben werden")
        
        self.students.update(student_id, first_name, last_name)

    def delete_student(self, student_id: int) -> None:
        """Löscht einen Schüler aus der Datenbank.
        
        DEPRECATED: Verwende self.students.delete() stattdessen.
        """
        self.students.delete(student_id)
    
    def get_students_by_course(self, course_id: int, semester_id: int) -> list:
        """Holt alle Schüler eines Kurses in einem bestimmten Semester.
        
        DEPRECATED: Verwende self.students.get_by_course() stattdessen.
        """
        return self.students.get_by_course(course_id, semester_id)

    def add_lesson(self, data: dict) -> int or list:
        """Fügt eine neue Unterrichtsstunde hinzu.
        
        DEPRECATED: Verwende self.lessons.add() stattdessen.
        """
        return self.lessons.add(data)

    def get_lessons_by_date(self, date: str) -> List[Dict[str, Any]]:
        """Holt alle Unterrichtsstunden für ein bestimmtes Datum.
        
        DEPRECATED: Verwende self.lessons.get_by_date() stattdessen.
        """
        return self.lessons.get_by_date(date)

    def get_all_lessons(self) -> List[Dict[str, Any]]:
        """Holt alle Unterrichtsstunden.
        
        DEPRECATED: Verwende self.lessons.get_all() stattdessen.
        """
        return self.lessons.get_all()

    def get_next_lesson_by_course(self, date: str) -> List[Dict[str, Any]]:
        """Holt für jeden Kurs die nächste anstehende Stunde nach einem Datum.
        
        DEPRECATED: Verwende self.lessons.get_next_by_course() stattdessen.
        """
        return self.lessons.get_next_by_course(date)

    # Kompetenz-bezogene Methoden
    def add_competency(self, data: dict) -> int:
        """Fügt eine neue Kompetenz hinzu."""
        try:
            cursor = self.execute(
                "INSERT INTO competencies (subject, area, description) VALUES (?, ?, ?)",
                (data['subject'], data['area'], data['description'])
            )
            return cursor.lastrowid
        except sqlite3.Error as e:
            raise Exception(f"Fehler beim Hinzufügen der Kompetenz: {e}")

    def get_competencies_by_subject(self, subject: str) -> List[Dict[str, Any]]:
        """Holt alle Kompetenzen für ein bestimmtes Fach."""
        cursor = self.execute(
            "SELECT * FROM competencies WHERE subject = ? ORDER BY area",
            (subject,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_all_competencies(self) -> list:
        """Holt alle Kompetenzen aus der Datenbank."""
        try:
            cursor = self.execute(
                "SELECT id, subject, area, description FROM competencies ORDER BY subject, area"
            )
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise Exception(f"Fehler beim Abrufen der Kompetenzen: {e}")

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

    # Einstellungs-bezogene Methoden (delegieren an SemesterRepository)
    def save_semester_dates(self, start_date: str, end_date: str) -> None:
        """Speichert die Semesterdaten.
        
        DEPRECATED: Verwende self.semesters.save_current() stattdessen.
        """
        self.semesters.save_current(start_date, end_date)

    def get_semester_dates(self) -> dict:
        """Holt die aktuellen Semesterdaten.
        
        DEPRECATED: Verwende self.semesters.get_current() stattdessen.
        """
        return self.semesters.get_current()
    
    def save_semester_to_history(self, start_date: str, end_date: str, 
                                 name: str = None, notes: str = None) -> int:
        """Speichert ein Halbjahr in der Historie.
        
        DEPRECATED: Verwende self.semesters.save_to_history() stattdessen.
        """
        return self.semesters.save_to_history(start_date, end_date, name, notes)
    
    def get_semester_history(self) -> list:
        """Holt alle gespeicherten Halbjahre.
        
        DEPRECATED: Verwende self.semesters.get_history() stattdessen.
        """
        return self.semesters.get_history()
    
    def get_semester_by_date(self, date: str) -> dict:
        """Findet das Halbjahr zu einem bestimmten Datum.
        
        DEPRECATED: Verwende self.semesters.get_by_date() stattdessen.
        """
        result = self.semesters.get_by_date(date)
        return result if result else None
    
    def delete_semester_from_history(self, semester_id: int) -> None:
        """Löscht ein Halbjahr aus der Historie.
        
        DEPRECATED: Verwende self.semesters.delete_from_history() stattdessen.
        """
        self.semesters.delete_from_history(semester_id)

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

    def get_student_grades(self, student_id: int, timeframe: str = None) -> list:
        """Holt alle Noten eines Schülers mit optionalem Zeitrahmen."""
        try:
            query = '''
                SELECT 
                    g.*,
                    l.date as lesson_date,
                    l.subject,
                    c.area as competency_area,
                    c.description as competency_description
                FROM grades g
                JOIN lessons l ON g.lesson_id = l.id
                JOIN competencies c ON g.competency_id = c.id
                WHERE g.student_id = ?
            '''
            params = [student_id]
            
            if timeframe:
                query += " AND l.date >= ?"
                params.append(timeframe)
                
            query += " ORDER BY l.date DESC"
            
            cursor = self.execute(query, tuple(params))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise Exception(f"Fehler beim Abrufen der Noten: {e}")

    # def get_grade_statistics(self, student_id: int) -> dict:
    #     """Berechnet Notenstatistiken für einen Schüler."""
    #     try:
    #         cursor = self.execute('''
    #             SELECT 
    #                 l.subject,
    #                 COUNT(*) as count,
    #                 AVG(g.grade * g.weight) as weighted_average,
    #                 MIN(g.grade) as best_grade,
    #                 MAX(g.grade) as worst_grade
    #             FROM grades g
    #             JOIN lessons l ON g.lesson_id = l.id
    #             WHERE g.student_id = ?
    #             GROUP BY l.subject
    #         ''', (student_id,))
            
    #         return {row['subject']: dict(row) for row in cursor.fetchall()}
    #     except sqlite3.Error as e:
    #         raise Exception(f"Fehler beim Berechnen der Statistiken: {e}")

    # def update_grade(self, grade_id: int, data: dict) -> None:
    #     """Aktualisiert eine bestehende Note."""
    #     try:
    #         fields = []
    #         values = []
    #         for key, value in data.items():
    #             if key not in ['id', 'created_at']:
    #                 fields.append(f"{key} = ?")
    #                 values.append(value)
            
    #         values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))  # updated_at
    #         values.append(grade_id)  # WHERE id = ?
            
    #         query = f'''
    #             UPDATE grades 
    #             SET {', '.join(fields)}, updated_at = ?
    #             WHERE id = ?
    #         '''
            
    #         self.execute(query, tuple(values))
    #     except sqlite3.Error as e:
    #         raise Exception(f"Fehler beim Aktualisieren der Note: {e}")

    # def get_grade(self, grade_id: int) -> dict:
    #     """Holt eine einzelne Note mit allen Details."""
    #     try:
    #         cursor = self.execute('''
    #             SELECT 
    #                 g.*,
    #                 l.date as lesson_date,
    #                 l.subject,
    #                 c.area as competency_area,
    #                 c.description as competency_description
    #             FROM grades g
    #             JOIN lessons l ON g.lesson_id = l.id
    #             JOIN competencies c ON g.competency_id = c.id
    #             WHERE g.id = ?
    #         ''', (grade_id,))
            
    #         result = cursor.fetchone()
    #         return dict(result) if result else None
    #     except sqlite3.Error as e:
    #         raise Exception(f"Fehler beim Abrufen der Note: {e}")

    def add_lesson_competency(self, lesson_id: int, competency_id: int) -> None:
        """Fügt eine Verknüpfung zwischen Unterrichtsstunde und Kompetenz hinzu.
        
        DEPRECATED: Verwende self.lessons.add_competency() stattdessen.
        """
        self.lessons.add_competency(lesson_id, competency_id)

    def get_lesson(self, lesson_id: int) -> dict:
        """Holt eine einzelne Unterrichtsstunde.
        
        DEPRECATED: Verwende self.lessons.get_by_id() stattdessen.
        """
        result = self.lessons.get_by_id(lesson_id)
        return result if result else None

    def get_competency(self, comp_id: int) -> dict:
        """Holt eine einzelne Kompetenz.
        
        DEPRECATED: Verwende self.competencies.get_by_id() stattdessen.
        """
        result = self.competencies.get_by_id(comp_id)
        return result if result else None

    def update_lesson(self, lesson_id: int, data: dict, update_all_following: bool = False) -> List[int]:
        """Aktualisiert eine oder mehrere Unterrichtsstunden.
        
        DEPRECATED: Verwende self.lessons.update() stattdessen.
        """
        return self.lessons.update(lesson_id, data, update_all_following)




    def get_all_courses(self) -> list:
        """Holt alle verfügbaren Kurse und Klassen.
        
        DEPRECATED: Verwende self.courses.get_all() stattdessen.
        """
        return self.courses.get_all()
    
    def get_courses_by_semester(self, semester_id: int) -> list:
        """Holt alle Kurse eines bestimmten Semesters.
        
        DEPRECATED: Verwende self.courses.get_by_semester() stattdessen.
        """
        return self.courses.get_by_semester(semester_id)


    def get_time_settings(self) -> dict:
        """Holt die Zeiteinstellungen aus der Datenbank.
        
        DEPRECATED: Verwende self.settings.get_time_settings() stattdessen.
        """
        return self.settings.get_time_settings()


    def get_previous_lesson_homework(self, course_id: int, date: str, time: str) -> Optional[str]:
        """Holt die Hausaufgaben der vorherigen Stunde eines Kurses.
        
        DEPRECATED: Verwende self.lessons.get_previous_homework() stattdessen.
        """
        return self.lessons.get_previous_homework(course_id, date, time)

    def get_courses_by_semester(self, semester_id: int) -> list:
        """Holt alle Kurse eines bestimmten Semesters."""
        try:
            query = """
            SELECT 
                c.*,
                COUNT(DISTINCT sc.student_id) as student_count
            FROM courses c
            LEFT JOIN student_courses sc ON c.id = sc.course_id AND sc.semester_id = ?
            GROUP BY c.id
            ORDER BY c.name
            """
            cursor = self.execute(query, (semester_id,))
            results = [dict(row) for row in cursor.fetchall()]
            return results
        except Exception as e:
            raise Exception(f"Fehler beim Laden der Kurse: {str(e)}")


    def get_students_by_course(self, course_id: int, semester_id: int) -> list:
        """Holt alle Schüler eines Kurses in einem bestimmten Semester."""
        try:
            query = """
            SELECT
                s.id,
                s.first_name,
                s.last_name
            FROM students s
            JOIN student_courses sc ON s.id = sc.student_id
            WHERE sc.course_id = ?
            AND sc.semester_id = ?
            ORDER BY s.last_name, s.first_name
            """
            cursor = self.execute(query, (course_id, semester_id))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            raise Exception(f"Fehler beim Laden der Schüler: {str(e)}")


# Neue Methoden für die Verwaltung von Notensystemen (delegieren an GradingSystemRepository):

    def add_grading_system(self, name: str, min_grade: float, max_grade: float, 
                          step_size: float, description: str = None) -> int:
        """Fügt ein neues Notensystem hinzu.
        
        DEPRECATED: Verwende self.grading_systems.add() stattdessen.
        """
        return self.grading_systems.add(name, min_grade, max_grade, step_size, description)

    def get_grading_system(self, system_id: int) -> dict:
        """Holt ein einzelnes Notensystem.
        
        DEPRECATED: Verwende self.grading_systems.get_by_id() stattdessen.
        """
        result = self.grading_systems.get_by_id(system_id)
        return result if result else None

    def get_all_grading_systems(self) -> list:
        """Holt alle verfügbaren Notensysteme.
        
        DEPRECATED: Verwende self.grading_systems.get_all() stattdessen.
        """
        return self.grading_systems.get_all()

    def update_grading_system(self, system_id: int, name: str, min_grade: float,
                            max_grade: float, step_size: float, description: str = None) -> None:
        """Aktualisiert ein bestehendes Notensystem.
        
        DEPRECATED: Verwende self.grading_systems.update() stattdessen.
        """
        self.grading_systems.update(system_id, name, min_grade, max_grade, step_size, description)

    def delete_grading_system(self, system_id: int) -> None:
        """Löscht ein Notensystem.
        
        DEPRECATED: Verwende self.grading_systems.delete() stattdessen.
        """
        self.grading_systems.delete(system_id)

    def validate_grade(self, grade: float, system_id: int) -> bool:
        """Prüft ob eine Note in einem Notensystem gültig ist.
        
        DEPRECATED: Verwende self.grading_systems.validate_grade() stattdessen.
        """
        return self.grading_systems.validate_grade(grade, system_id)
    
    def get_course_grading_system(self, course_id: int) -> dict:
        """Holt das Notensystem für einen Kurs über dessen Template.
        
        DEPRECATED: Verwende self.grading_systems.get_by_course() stattdessen.
        """
        result = self.grading_systems.get_by_course(course_id)
        return result if result else None

# Neue Methoden für die Verwaltung von Templates:

    def add_assessment_template(self, name: str, subject: str, 
                              grading_system_id: int, description: str = None) -> int:
        """Fügt eine neue Bewertungstyp-Vorlage hinzu.
        
        DEPRECATED: Verwende self.assessment_templates.add() stattdessen.
        """
        return self.assessment_templates.add(name, subject, grading_system_id, description)

    def add_template_item(self, template_id: int, name: str, 
                         parent_item_id: int = None, default_weight: float = 1.0) -> int:
        """Fügt einen Bewertungstyp zu einer Vorlage hinzu.
        
        DEPRECATED: Verwende self.assessment_templates.add_item() stattdessen.
        """
        return self.assessment_templates.add_item(template_id, name, parent_item_id, default_weight)

    def get_assessment_template(self, template_id: int) -> dict:
        """Holt eine einzelne Bewertungstyp-Vorlage.
        
        DEPRECATED: Verwende self.assessment_templates.get_by_id() stattdessen.
        """
        result = self.assessment_templates.get_by_id(template_id)
        return result if result else None

    def get_template_items(self, template_id: int) -> list:
        """Holt alle Bewertungstypen einer Vorlage hierarchisch sortiert.
        
        DEPRECATED: Verwende self.assessment_templates.get_items() stattdessen.
        """
        return self.assessment_templates.get_items(template_id)

    def get_templates_by_subject(self, subject: str) -> list:
        """Holt alle Vorlagen für ein bestimmtes Fach.
        
        DEPRECATED: Verwende self.assessment_templates.get_by_subject() stattdessen.
        """
        return self.assessment_templates.get_by_subject(subject)

    def update_assessment_template(self, template_id: int, name: str, 
                                 subject: str, grading_system_id: int, 
                                 description: str = None) -> None:
        """Aktualisiert eine bestehende Vorlage.
        
        DEPRECATED: Verwende self.assessment_templates.update() stattdessen.
        """
        self.assessment_templates.update(template_id, name, subject, grading_system_id, description)

    def update_template_item(self, item_id: int, name: str, 
                           parent_item_id: int = None, 
                           default_weight: float = 1.0) -> None:
        """Aktualisiert ein Vorlagenelement.
        
        DEPRECATED: Verwende self.assessment_templates.update_item() stattdessen.
        """
        self.assessment_templates.update_item(item_id, name, parent_item_id, default_weight)

    def delete_assessment_template(self, template_id: int) -> None:
        """Löscht eine Vorlage und alle ihre Elemente.
        
        DEPRECATED: Verwende self.assessment_templates.delete() stattdessen.
        """
        self.assessment_templates.delete(template_id)

    def delete_template_item(self, item_id: int) -> None:
        """Löscht ein Vorlagenelement.
        
        DEPRECATED: Verwende self.assessment_templates.delete_item() stattdessen.
        """
        self.assessment_templates.delete_item(item_id)
    
    def get_all_assessment_templates(self) -> list:
        """Holt alle Bewertungsvorlagen mit zugehörigen Notensystemen.
        
        DEPRECATED: Verwende self.assessment_templates.get_all() stattdessen.
        """
        return self.assessment_templates.get_all()


# Neue Methoden für die Verwaltung von Assessment Types:

    def create_assessment_types_from_template(self, course_id: int, template_id: int) -> None:
        """Erstellt Bewertungstypen für einen Kurs basierend auf einer Vorlage.
        
        DEPRECATED: Verwende self.assessment_types.create_from_template() stattdessen.
        """
        self.assessment_types.create_from_template(course_id, template_id)

    def add_assessment_type(self, course_id: int, name: str, 
                          parent_type_id: int = None, weight: float = 1.0) -> int:
        """Fügt einen neuen Bewertungstyp hinzu.
        
        DEPRECATED: Verwende self.assessment_types.add() stattdessen.
        """
        return self.assessment_types.add(course_id, name, parent_type_id, weight)

    def get_assessment_types(self, course_id: int) -> list:
        """Holt alle Bewertungstypen eines Kurses hierarchisch sortiert.
        
        DEPRECATED: Verwende self.assessment_types.get_by_course() stattdessen.
        """
        return self.assessment_types.get_by_course(course_id)

    def delete_assessment_type(self, type_id: int) -> None:
        """Löscht einen Bewertungstyp und alle zugehörigen Untertypen.
        
        DEPRECATED: Verwende self.assessment_types.delete() stattdessen.
        """
        self.assessment_types.delete(type_id)

# Neue Methoden für die Verwaltung von Assessments (Noten):

# In db_manager.py

    def validate_assessment_input(self, student_id: int, course_id: int, 
                                assessment_type_id: int, grade: float, 
                                date: str) -> None:
        """
        Validiert die Eingabedaten für eine neue Note.
        Wirft eine Exception wenn die Daten ungültig sind.
        """
        try:
            # 1. Prüfe ob der Schüler im Kurs ist
            cursor = self.execute(
                """SELECT semester_id, start_date, end_date 
                   FROM student_courses sc
                   JOIN semester_history sh ON sc.semester_id = sh.id
                   WHERE student_id = ? AND course_id = ?
                   AND start_date <= ? AND end_date >= ?""",
                (student_id, course_id, date, date)
            )
            if not cursor.fetchone():
                raise ValueError(
                    f"Der Schüler (ID: {student_id}) ist zu diesem Zeitpunkt "
                    f"nicht im Kurs (ID: {course_id})"
                )

            # 2. Prüfe ob der Bewertungstyp zum Kurs gehört
            cursor = self.execute(
                "SELECT id FROM assessment_types WHERE id = ? AND course_id = ?",
                (assessment_type_id, course_id)
            )
            if not cursor.fetchone():
                raise ValueError(
                    f"Der Bewertungstyp (ID: {assessment_type_id}) gehört "
                    f"nicht zum Kurs (ID: {course_id})"
                )

            # 3. Prüfe ob die Note zum Notensystem passt
            cursor = self.execute(
                """SELECT gs.* 
                   FROM assessment_type_templates att
                   JOIN grading_systems gs ON att.grading_system_id = gs.id
                   WHERE att.id = ?""",
                (assessment_type_id,)
            )
            grading_system = cursor.fetchone()
            if grading_system:
                if not self.validate_grade(grade, grading_system['id']):
                    raise ValueError(
                        f"Die Note {grade} ist im Notensystem "
                        f"'{grading_system['name']}' nicht gültig"
                    )

        except Exception as e:
            raise ValueError(f"Validierungsfehler: {str(e)}")

    def get_assessment_statistics(self, course_id: int, 
                                start_date: str = None, 
                                end_date: str = None) -> dict:
        """
        Berechnet verschiedene Statistiken für einen Kurs.
        
        Returns:
            Dict mit verschiedenen statistischen Werten.
        """
        try:
            # Basisteil der Query
            query = """
                SELECT 
                    COUNT(*) as total_count,
                    AVG(a.grade) as average_grade,
                    MIN(a.grade) as best_grade,
                    MAX(a.grade) as worst_grade,
                    a.assessment_type_id,
                    t.name as type_name
                FROM assessments a
                JOIN assessment_types t ON a.assessment_type_id = t.id
                WHERE a.course_id = ?
            """
            params = [course_id]

            # Zeitraum-Filter hinzufügen wenn angegeben
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)

            # Gruppierung nach Bewertungstyp
            query += " GROUP BY assessment_type_id"

            cursor = self.execute(query, tuple(params))
            type_stats = {row['type_name']: dict(row) for row in cursor.fetchall()}

            # Gesamtstatistik
            total_query = """
                SELECT 
                    COUNT(*) as total_count,
                    AVG(a.grade) as average_grade,
                    MIN(a.grade) as best_grade,
                    MAX(a.grade) as worst_grade
                FROM assessments a
                WHERE a.course_id = ?
            """
            if start_date:
                total_query += " AND date >= ?"
            if end_date:
                total_query += " AND date <= ?"

            cursor = self.execute(total_query, tuple(params))
            total_stats = dict(cursor.fetchone())

            return {
                'total': total_stats,
                'by_type': type_stats
            }

        except Exception as e:
            raise Exception(f"Fehler bei der Berechnung der Statistik: {str(e)}")

    def get_student_grade_history(self, student_id: int, course_id: int, 
                                assessment_type_id: int = None) -> list:
        """
        Holt die Notenentwicklung eines Schülers.
        
        Args:
            student_id: ID des Schülers
            course_id: ID des Kurses
            assessment_type_id: Optional, für einen bestimmten Bewertungstyp

        Returns:
            Liste von Noten, chronologisch sortiert
        """
        try:
            query = """
                SELECT 
                    a.*,
                    t.name as type_name,
                    t.weight as type_weight
                FROM assessments a
                JOIN assessment_types t ON a.assessment_type_id = t.id
                WHERE a.student_id = ? AND a.course_id = ?
            """
            params = [student_id, course_id]

            if assessment_type_id:
                query += " AND a.assessment_type_id = ?"
                params.append(assessment_type_id)

            query += " ORDER BY a.date"

            cursor = self.execute(query, tuple(params))
            return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            raise Exception(f"Fehler beim Abrufen der Notenhistorie: {str(e)}")

    def get_course_grade_export(self, course_id: int) -> dict:
        """
        Erstellt eine exportierbare Übersicht aller Noten eines Kurses.
        
        Returns:
            Dict mit Kursinformationen und Notendaten
        """
        try:
            # 1. Kursinformationen
            cursor = self.execute(
                "SELECT * FROM courses WHERE id = ?",
                (course_id,)
            )
            course = dict(cursor.fetchone())

            # 2. Bewertungstypen (hierarchisch)
            types = self.get_assessment_types(course_id)

            # 3. Schüler im Kurs
            cursor = self.execute(
                """SELECT DISTINCT s.* 
                   FROM students s
                   JOIN student_courses sc ON s.id = sc.student_id
                   WHERE sc.course_id = ?
                   ORDER BY s.last_name, s.first_name""",
                (course_id,)
            )
            students = [dict(row) for row in cursor.fetchall()]

            # 4. Alle Noten
            cursor = self.execute(
                """SELECT 
                       a.*,
                       t.name as type_name,
                       s.last_name,
                       s.first_name
                   FROM assessments a
                   JOIN assessment_types t ON a.assessment_type_id = t.id
                   JOIN students s ON a.student_id = s.id
                   WHERE a.course_id = ?
                   ORDER BY s.last_name, s.first_name, a.date""",
                (course_id,)
            )
            grades = [dict(row) for row in cursor.fetchall()]

            # 5. Statistiken
            statistics = self.get_assessment_statistics(course_id)

            return {
                'course': course,
                'types': types,
                'students': students,
                'grades': grades,
                'statistics': statistics
            }

        except Exception as e:
            raise Exception(f"Fehler beim Erstellen der Exportdaten: {str(e)}")

    def get_course_grading_system(self, course_id: int) -> dict:
        """Holt das Notensystem für einen Kurs über dessen Template."""
        try:
            cursor = self.execute(
                """SELECT gs.* 
                FROM courses c
                JOIN assessment_type_templates att ON c.template_id = att.id
                JOIN grading_systems gs ON att.grading_system_id = gs.id
                WHERE c.id = ?""",
                (course_id,)
            )
            result = cursor.fetchone()
            return dict(result) if result else None
        except Exception as e:
            print(f"Error getting grading system: {str(e)}")
            return None

    def add_assessment(self, data: dict) -> int:
        """Fügt eine neue Bewertung/Note hinzu oder aktualisiert eine bestehende.
        
        DEPRECATED: Verwende self.assessments.add_or_update() stattdessen.
        """
        return self.assessments.add_or_update(data)

    def delete_assessment(self, student_id: int, lesson_id: int) -> None:
        """Löscht eine Note für einen Schüler in einer bestimmten Stunde.
        
        DEPRECATED: Verwende self.assessments.delete() stattdessen.
        """
        self.assessments.delete(student_id, lesson_id)

    def get_student_assessments(self, student_id: int, course_id: int) -> list:
        """Holt alle Noten eines Schülers in einem Kurs.
        
        DEPRECATED: Verwende self.assessments.get_by_student_and_course() stattdessen.
        """
        return self.assessments.get_by_student_and_course(student_id, course_id)

    def get_lesson_assessment(self, student_id: int, lesson_id: int) -> Optional[dict]:
        """Holt die Note eines Schülers für eine bestimmte Stunde.
        
        DEPRECATED: Verwende self.assessments.get_by_lesson() stattdessen.
        """
        return self.assessments.get_by_lesson(student_id, lesson_id)

    def get_course_assessments(self, course_id: int, assessment_type_id: int = None) -> list:
        """Holt alle Noten eines Kurses, optional gefiltert nach Bewertungstyp.
        
        DEPRECATED: Verwende self.assessments.get_by_course() stattdessen.
        """
        return self.assessments.get_by_course(course_id, assessment_type_id)

    def calculate_final_grade(self, student_id: int, course_id: int) -> float:
        """Berechnet die Gesamtnote eines Schülers in einem Kurs.
        
        DEPRECATED: Verwende self.assessments.calculate_final_grade() stattdessen.
        """
        return self.assessments.calculate_final_grade(student_id, course_id)

    def get_student_course_grades(self, student_id: int) -> dict:
        """Holt die Gesamtnoten eines Schülers für alle seine Kurse.
        
        DEPRECATED: Verwende self.assessments.get_student_course_grades() stattdessen.
        """
        return self.assessments.get_student_course_grades(student_id)

    def get_student_competency_grades(self, student_id: int) -> dict:
        """Berechnet die Durchschnittsnoten pro Kompetenzbereich für jeden Kurs eines Schülers.
        
        Returns:
            dict: {
                'areas': ['Bereich1', 'Bereich2', ...],  # Alle vorkommenden Kompetenzbereiche
                'grades': [  # Liste der Kurse mit ihren Kompetenznoten
                    {
                        'course_id': id,
                        'course_name': name,
                        'competencies': {
                            'Bereich1': note,
                            'Bereich2': note,
                            ...
                        }
                    },
                    ...
                ]
            }
        """
        try:
            # Erst alle vorkommenden Kompetenzbereiche ermitteln
            cursor = self.execute("""
                SELECT DISTINCT comp.area
                FROM assessments a
                JOIN lessons l ON a.lesson_id = l.id
                JOIN lesson_competencies lc ON l.id = lc.lesson_id
                JOIN competencies comp ON lc.competency_id = comp.id
                WHERE a.student_id = ?
                ORDER BY comp.area
            """, (student_id,))
            
            comp_areas = [row['area'] for row in cursor.fetchall()]
            
            # Dann die Noten pro Kurs und Kompetenzbereich holen
            cursor = self.execute("""
                SELECT 
                    c.id as course_id,
                    c.name as course_name,
                    comp.area as comp_area,
                    (SUM(a.grade * a.weight) / SUM(a.weight)) as avg_grade
                FROM assessments a
                JOIN courses c ON a.course_id = c.id
                JOIN lessons l ON a.lesson_id = l.id
                JOIN lesson_competencies lc ON l.id = lc.lesson_id
                JOIN competencies comp ON lc.competency_id = comp.id
                WHERE a.student_id = ?
                GROUP BY c.id, c.name, comp.area
                ORDER BY c.name, comp.area
            """, (student_id,))
            
            # Ergebnisse strukturieren
            grades_data = {}
            for row in cursor.fetchall():
                course_id = row['course_id']
                if course_id not in grades_data:
                    grades_data[course_id] = {
                        'course_id': course_id,
                        'course_name': row['course_name'],
                        'competencies': {}
                    }
                grades_data[course_id]['competencies'][row['comp_area']] = row['avg_grade']
            
            return {
                'areas': comp_areas,
                'grades': list(grades_data.values())
            }
            
        except Exception as e:
            print(f"DEBUG: Error in get_student_competency_grades: {str(e)}")
            raise

    def get_student_assessment_type_grades(self, student_id: int, course_id: int) -> list:
        """Holt die Durchschnittsnoten pro Assessment Type für einen bestimmten Kurs.
        
        DEPRECATED: Verwende self.assessments.get_by_assessment_type() stattdessen.
        """
        return self.assessments.get_by_assessment_type(student_id, course_id)
        
    def mark_student_absent(self, lesson_id: int, student_id: int) -> None:
        """Markiert einen Schüler als abwesend für eine Stunde.
        
        DEPRECATED: Verwende self.attendance.mark_absent() stattdessen.
        """
        self.attendance.mark_absent(lesson_id, student_id)

    def mark_student_present(self, lesson_id: int, student_id: int) -> None:
        """Löscht einen Abwesenheitseintrag (= Schüler war anwesend).
        
        DEPRECATED: Verwende self.attendance.mark_present() stattdessen.
        """
        self.attendance.mark_present(lesson_id, student_id)

    def get_absent_students(self, lesson_id: int) -> List[int]:
        """Holt die IDs aller abwesenden Schüler für eine Stunde.
        
        DEPRECATED: Verwende self.attendance.get_absent_students() stattdessen.
        """
        return self.attendance.get_absent_students(lesson_id)


    def get_all_assessment_templates(self) -> list:
        """Holt alle Bewertungsvorlagen mit zugehörigen Notensystemen."""
        cursor = self.execute(
            """SELECT t.*, g.name as grading_system_name
            FROM assessment_type_templates t
            JOIN grading_systems g ON t.grading_system_id = g.id
            ORDER BY t.subject, t.name"""
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_assessment_template(self, template_id: int) -> dict:
        """Holt eine einzelne Vorlage."""
        cursor = self.execute(
            """SELECT t.*, g.name as grading_system_name 
            FROM assessment_type_templates t
            JOIN grading_systems g ON t.grading_system_id = g.id
            WHERE t.id = ?""",
            (template_id,)
        )
        result = cursor.fetchone()
        return dict(result) if result else None

    def add_assessment_template(self, name: str, subject: str, 
                            grading_system_id: int, description: str = None) -> int:
        """Fügt eine neue Vorlage hinzu."""
        cursor = self.execute(
            """INSERT INTO assessment_type_templates 
            (name, subject, grading_system_id, description)
            VALUES (?, ?, ?, ?)""",
            (name, subject, grading_system_id, description)
        )
        return cursor.lastrowid

    def update_assessment_template(self, template_id: int, name: str, subject: str,
                                grading_system_id: int, description: str = None) -> None:
        """Aktualisiert eine bestehende Vorlage."""
        self.execute(
            """UPDATE assessment_type_templates 
            SET name = ?, subject = ?, grading_system_id = ?, description = ?
            WHERE id = ?""",
            (name, subject, grading_system_id, description, template_id)
        )

    def delete_assessment_template(self, template_id: int) -> None:
        """Löscht eine Vorlage und alle ihre Items."""
        try:
            # Zuerst die Template-Items löschen
            self.execute(
                "DELETE FROM template_items WHERE template_id = ?",
                (template_id,)
            )
            
            # Dann das Template selbst löschen
            self.execute(
                "DELETE FROM assessment_type_templates WHERE id = ?",
                (template_id,)
            )
        except Exception as e:
            raise Exception(f"Fehler beim Löschen der Vorlage: {str(e)}")



    def add_public_holiday(self, date: str, name: str, type: str, state: str, year: int) -> int:
        """Fügt einen neuen Feiertag/Ferientag hinzu.
        
        DEPRECATED: Verwende self.holidays.add_public() stattdessen.
        """
        return self.holidays.add_public(date, name, type, state, year)

    def add_school_holiday(self, date: str, name: str, description: str = None) -> int:
        """Fügt einen schulspezifischen freien Tag hinzu.
        
        DEPRECATED: Verwende self.holidays.add_school() stattdessen.
        """
        return self.holidays.add_school(date, name, description)

    def delete_public_holiday(self, holiday_id: int) -> None:
        """Löscht einen Feiertag/Ferientag.
        
        DEPRECATED: Verwende self.holidays.delete_public() stattdessen.
        """
        self.holidays.delete_public(holiday_id)

    def delete_school_holiday(self, holiday_id: int) -> None:
        """Löscht einen schulspezifischen freien Tag.
        
        DEPRECATED: Verwende self.holidays.delete_school() stattdessen.
        """
        self.holidays.delete_school(holiday_id)

    def get_holidays_by_date_range(self, start_date: str, end_date: str) -> list:
        """Holt alle Feiertage und freien Tage in einem Zeitraum.
        
        DEPRECATED: Verwende self.holidays.get_by_date_range() stattdessen.
        """
        return self.holidays.get_by_date_range(start_date, end_date)

    def clear_public_holidays(self, year: int, state: str) -> None:
        """Löscht alle öffentlichen Feiertage eines Jahres/Bundeslandes.
        
        DEPRECATED: Verwende self.holidays.clear_public_by_year() stattdessen.
        """
        self.holidays.clear_public_by_year(year, state)

    def get_school_holidays(self) -> list:
        """Holt alle schulspezifischen freien Tage.
        
        DEPRECATED: Verwende self.holidays.get_school_holidays() stattdessen.
        """
        return self.holidays.get_school_holidays()

    def get_public_holidays_by_year(self, year: int, state: str) -> list:
        """Holt alle öffentlichen Feiertage/Ferien eines Jahres.
        
        DEPRECATED: Verwende self.holidays.get_public_by_year() stattdessen.
        """
        return self.holidays.get_public_by_year(year, state)

    def update_lesson_status_for_holidays(self):
        """Aktualisiert den Status von Stunden, die in Ferien/an Feiertagen liegen.
        
        DEPRECATED: Verwende self.holidays.update_lesson_status_for_holidays() stattdessen.
        """
        self.holidays.update_lesson_status_for_holidays()