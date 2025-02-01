# src/database/db_manager.py

import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta  # timedelta hier hinzugefügt

class DatabaseManager:
    def __init__(self, db_file: str = "school.db"):
        self.db_file = db_file
        self.conn = None
        self.connect()
        self.setup_tables()
    
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
                    FOREIGN KEY (template_id) REFERENCES assessment_type_templates(id)
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

            # Prüfe ob die template_id Spalte existiert, wenn nicht füge sie hinzu
            try:
                cursor.execute("ALTER TABLE courses ADD COLUMN template_id INTEGER REFERENCES assessment_type_templates(id)")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e).lower():
                    raise e

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
        

    # Student-bezogene Methoden
    def add_student(self, name: str) -> int:
        """Fügt einen neuen Schüler hinzu und gibt seine ID zurück."""
        cursor = self.execute(
            "INSERT INTO students (name) VALUES (?)",
            (name,)
        )
        return cursor.lastrowid

    def get_student(self, student_id: int) -> Optional[Dict[str, Any]]:
        """Holt einen einzelnen Schüler anhand seiner ID."""
        cursor = self.execute(
            "SELECT * FROM students WHERE id = ?",
            (student_id,)
        )
        return dict(cursor.fetchone()) if cursor.fetchone() else None

    def get_all_students(self) -> list:
        """Holt alle Schüler aus der Datenbank."""
        try:
            cursor = self.execute(
                "SELECT id, first_name, last_name FROM students ORDER BY last_name, first_name"
            )
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise Exception(f"Fehler beim Abrufen der Schüler: {e}")

    def update_student(self, student_id: int, name: str) -> None:
        """Aktualisiert die Daten eines Schülers."""
        self.execute(
            "UPDATE students SET name = ? WHERE id = ?",
            (name, student_id)
        )

    def delete_student(self, student_id: int) -> None:
        """Löscht einen Schüler aus der Datenbank."""
        self.execute(
            "DELETE FROM students WHERE id = ?",
            (student_id,)
        )

    def add_lesson(self, data: dict) -> int or list:
        try:
            if not data.get('course_id'):
                raise ValueError("Eine Unterrichtsstunde muss einem Kurs zugeordnet sein")
                
            if data.get('is_recurring'):
                # Semesterdaten holen
                semester = self.get_semester_dates()
                if not semester:
                    raise ValueError("Kein aktives Halbjahr gefunden")
                # Wochentag bestimmen
                start_date = datetime.strptime(data['date'], "%Y-%m-%d")
                weekday = start_date.isoweekday()
                # Hash generieren
                time_str = data['time'] if isinstance(data['time'], str) else data['time'][0]
                rec_hash = self.generate_recurring_hash(
                    data['course_id'],
                    weekday,
                    time_str
                )
                # Alle Termine bis Semesterende erstellen
                lesson_ids = []
                current_date = start_date
                end_date = datetime.strptime(semester['semester_end'], "%Y-%m-%d")
                
                while current_date <= end_date:
                    if current_date.isoweekday() == weekday:
                        cursor = self.execute(
                            """INSERT INTO lessons
                            (course_id, date, time, subject, topic, recurring_hash, duration)
                            VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (data['course_id'],
                            current_date.strftime("%Y-%m-%d"),
                            data['time'],
                            data['subject'],
                            data.get('topic', ''),
                            rec_hash,
                            data.get('duration', 1))
                        )
                        lesson_ids.append(cursor.lastrowid)
                    current_date += timedelta(days=1)
                return lesson_ids  # Gebe alle IDs zurück
            
            else:
                # Normale einzelne Unterrichtsstunde
                cursor = self.execute(
                    """INSERT INTO lessons
                    (course_id, date, time, subject, topic, duration)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (data['course_id'],
                    data['date'],
                    data['time'],
                    data['subject'],
                    data.get('topic', ''),
                    data.get('duration', 1))
                )
                return cursor.lastrowid
                
        except Exception as e:
            raise Exception(f"Fehler beim Hinzufügen der Unterrichtsstunde: {str(e)}")

    def get_lessons_by_date(self, date: str) -> List[Dict[str, Any]]:
        """Holt alle Unterrichtsstunden für ein bestimmtes Datum."""
        
        # Erst alle Lektionen anzeigen
        cursor = self.execute("SELECT DISTINCT date FROM lessons ORDER BY date")
        dates = [row['date'] for row in cursor.fetchall()]
        
        # Dann die eigentliche Query
        query = """
            SELECT 
                l.*,
                c.name as course_name,
                c.color as course_color
            FROM lessons l
            JOIN courses c ON l.course_id = c.id
            WHERE l.date = ?
        """
        
        cursor = self.execute(query, (date,))
        results = [dict(row) for row in cursor.fetchall()]
        return results

    def get_all_lessons(self) -> List[Dict[str, Any]]:
            """Holt alle Unterrichtsstunden."""
            cursor = self.execute(
                "SELECT * FROM lessons ORDER BY date, time"
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_next_lesson_by_course(self, date: str) -> List[Dict[str, Any]]:
        """Holt für jeden Kurs die nächste anstehende Stunde nach einem Datum."""
        try:
            query = """
                SELECT 
                    l.*,
                    c.name as course_name,
                    c.color as course_color
                FROM lessons l
                JOIN courses c ON l.course_id = c.id
                WHERE l.date >= ?
                ORDER BY l.date, l.time
            """
            cursor = self.execute(query, (date,))
            all_lessons = [dict(row) for row in cursor.fetchall()]
            
            # Dictionary für die nächsten Stunden pro Kurs
            next_lessons = {}
            current_time = datetime.now()
            current_time_str = current_time.strftime("%H:%M")
            
            # Hole Zeiteinstellungen für Stundenlänge
            settings = self.get_time_settings()
            lesson_duration = 45  # Standard-Stundenlänge in Minuten
            if settings and 'lesson_duration' in settings:
                lesson_duration = settings['lesson_duration']
            
            for lesson in all_lessons:
                course_id = lesson['course_id']
                if course_id in next_lessons:
                    continue
                    
                # Berechne Endzeit der Stunde
                lesson_time = datetime.strptime(lesson['time'], "%H:%M")
                lesson_end = (lesson_time + timedelta(minutes=lesson_duration * 
                                                    (lesson.get('duration', 1)))).time()
                
                # Überspringe Stunden vom aktuellen Tag die schon vorbei sind
                if (lesson['date'] == date and 
                    lesson_end.strftime("%H:%M") <= current_time_str):
                    continue
                    
                next_lessons[course_id] = lesson
                
            return list(next_lessons.values())
                    
        except Exception as e:
            raise Exception(f"Fehler beim Laden der nächsten Stunden: {str(e)}")

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

    # Einstellungs-bezogene Methoden
    def save_semester_dates(self, start_date: str, end_date: str) -> None:
        """Speichert die Semesterdaten."""
        self.execute(
            """INSERT OR REPLACE INTO settings 
               (id, semester_start, semester_end)
               VALUES (1, ?, ?)""",
            (start_date, end_date)
        )

    def get_semester_dates(self) -> dict:
        """Holt die aktuellen Semesterdaten."""
        cursor = self.execute(
            "SELECT semester_start, semester_end FROM settings WHERE id = 1"
        )
        row = cursor.fetchone()
        if row:
            return {
                'semester_start': row['semester_start'],
                'semester_end': row['semester_end']
            }
        return None

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
        """Fügt eine Verknüpfung zwischen Unterrichtsstunde und Kompetenz hinzu."""
        try:
            self.execute(
                "INSERT INTO lesson_competencies (lesson_id, competency_id) VALUES (?, ?)",
                (lesson_id, competency_id)
            )
        except sqlite3.IntegrityError:
            # Falls die Verknüpfung bereits existiert, ignorieren wir den Fehler
            pass
        except Exception as e:
            raise Exception(f"Fehler beim Verknüpfen von Stunde und Kompetenz: {str(e)}")

    def get_lesson(self, lesson_id: int) -> dict:
            """Holt eine einzelne Unterrichtsstunde."""
            cursor = self.execute(
                "SELECT * FROM lessons WHERE id = ?",
                (lesson_id,)
            )
            result = cursor.fetchone()
            return dict(result) if result else None

    def get_competency(self, comp_id: int) -> dict:
        """Holt eine einzelne Kompetenz."""
        cursor = self.execute(
            "SELECT * FROM competencies WHERE id = ?",
            (comp_id,)
        )
        result = cursor.fetchone()
        return dict(result) if result else None

    def update_lesson(self, lesson_id: int, data: dict, update_all_following: bool = False) -> List[int]:
        """Aktualisiert eine oder mehrere Unterrichtsstunden.
        
        Args:
            lesson_id: ID der zu ändernden Stunde
            data: Dictionary mit den neuen Daten (course_id, date, time, subject, topic)
            update_all_following: Bool, ob alle folgenden Stunden auch geändert werden sollen
            
        Returns:
            Liste der IDs aller geänderten Stunden
        """
        try:
            # Aktuelle Stunde und deren Hash holen
            current_lesson = self.get_lesson(lesson_id)
            if not current_lesson:
                raise ValueError("Stunde nicht gefunden")
                
            if update_all_following and current_lesson['recurring_hash']:
                # Aktualisiere alle folgenden Stunden mit gleichem Hash
                update_fields = []
                values = []
                for key, value in data.items():
                    if key not in ['id', 'created_at', 'date']:  # date nicht ändern!
                        update_fields.append(f"{key} = ?")
                        values.append(value)
                
                # Füge WHERE-Klausel Parameter hinzu
                values.extend([
                    current_lesson['recurring_hash'],
                    current_lesson['date']  # Nur Stunden ab dem aktuellen Datum
                ])
                
                query = f"""
                    UPDATE lessons 
                    SET {', '.join(update_fields)}
                    WHERE recurring_hash = ?
                    AND date >= ?
                """
                
                self.execute(query, tuple(values))
                
                # Hole IDs aller geänderten Stunden
                cursor = self.execute(
                    """SELECT id FROM lessons 
                    WHERE recurring_hash = ? 
                    AND date >= ?""",
                    (current_lesson['recurring_hash'], 
                    current_lesson['date'])
                )
                return [row['id'] for row in cursor.fetchall()]
                
            else:
                # Nur einzelne Stunde aktualisieren
                update_fields = []
                values = []
                for key, value in data.items():
                    if key not in ['id', 'created_at', 'recurring_hash']:
                        update_fields.append(f"{key} = ?")
                        values.append(value)
                
                values.append(lesson_id)
                query = f"""
                    UPDATE lessons 
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                """
                
                self.execute(query, tuple(values))
                return [lesson_id]
                
        except Exception as e:
            raise Exception(f"Fehler beim Aktualisieren der Stunde(n): {str(e)}")


    def update_competency(self, comp_id: int, data: dict) -> None:
        """Aktualisiert eine Kompetenz."""
        self.execute(
            """UPDATE competencies 
            SET subject = ?, area = ?, description = ? 
            WHERE id = ?""",
            (data['subject'], data['area'], data['description'], comp_id)
        )
    def delete_student(self, student_id: int) -> None:
        """Löscht einen Schüler."""
        try:
            self.execute("DELETE FROM students WHERE id = ?", (student_id,))
        except sqlite3.Error as e:
            raise Exception(f"Fehler beim Löschen des Schülers: {e}")

    def delete_lessons(self, lesson_id: int, delete_all_following: bool = False) -> None:
        """Löscht eine oder mehrere Unterrichtsstunden.
        
        Args:
            lesson_id: ID der zu löschenden Stunde
            delete_all_following: Bool, ob alle folgenden Stunden auch gelöscht werden sollen
        """
        try:
            # Aktuelle Stunde und deren Hash holen
            current_lesson = self.get_lesson(lesson_id)
            if not current_lesson:
                raise ValueError("Stunde nicht gefunden")
                
            if delete_all_following and current_lesson['recurring_hash']:
                # Alle folgenden Stunden mit gleichem Hash löschen
                self.execute(
                    """DELETE FROM lessons 
                    WHERE recurring_hash = ?
                    AND date >= ?""",
                    (current_lesson['recurring_hash'],
                    current_lesson['date'])
                )
            else:
                # Nur einzelne Stunde löschen
                self.execute(
                    "DELETE FROM lessons WHERE id = ?",
                    (lesson_id,)
                )
                
        except Exception as e:
            raise Exception(f"Fehler beim Löschen der Stunde(n): {str(e)}")

    def delete_competency(self, comp_id: int) -> None:
        """Löscht eine Kompetenz."""
        try:
            self.execute("DELETE FROM competencies WHERE id = ?", (comp_id,))
            # Zugehörige Zuordnungen löschen
            self.execute("DELETE FROM lesson_competencies WHERE competency_id = ?", (comp_id,))
        except sqlite3.Error as e:
            raise Exception(f"Fehler beim Löschen der Kompetenz: {e}")


    def get_lesson(self, lesson_id: int) -> dict:
        """Holt eine einzelne Unterrichtsstunde mit Kursinformationen."""
        cursor = self.execute(
            """SELECT l.*, c.name as course_name, c.subject as course_subject
            FROM lessons l
            JOIN courses c ON l.course_id = c.id
            WHERE l.id = ?""",
            (lesson_id,)
        )
        result = cursor.fetchone()
        return dict(result) if result else None


    def save_semester_to_history(self, start_date: str, end_date: str, name: str = None, notes: str = None) -> int:
        """Speichert ein Halbjahr in der Historie."""
        cursor = self.execute(
            """INSERT INTO semester_history (start_date, end_date, name, notes)
            VALUES (?, ?, ?, ?)""",
            (start_date, end_date, name, notes)
        )
        return cursor.lastrowid

    def get_semester_history(self) -> list:
        """Holt alle gespeicherten Halbjahre."""
        cursor = self.execute(
            """SELECT * FROM semester_history 
            ORDER BY start_date DESC"""
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_semester_by_date(self, date: str) -> dict:
        """Findet das Halbjahr zu einem bestimmten Datum."""
        cursor = self.execute(
            """SELECT * FROM semester_history 
            WHERE start_date <= ? AND end_date >= ?
            ORDER BY start_date DESC LIMIT 1""",
            (date, date)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def delete_semester_from_history(self, semester_id: int) -> None:
        """Löscht ein Halbjahr aus der Historie."""
        self.execute(
            "DELETE FROM semester_history WHERE id = ?",
            (semester_id,)
        )


    def get_all_courses(self) -> list:
        """Holt alle verfügbaren Kurse und Klassen."""
        try:
            cursor = self.execute(
                """SELECT id, name, type, subject 
                   FROM courses 
                   ORDER BY name"""
            )
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            raise Exception(f"Fehler beim Abrufen der Kurse: {str(e)}")

    def generate_recurring_hash(self, course_id: int, weekday: int, time: str) -> str:
        """Generiert einen Hash für wiederkehrende Stunden.
        
        Args:
            course_id: ID des Kurses
            weekday: Wochentag als int (1=Montag, 7=Sonntag)
            time: Uhrzeit im Format "HH:MM"
            
        Returns:
            Hash-String für diese Kombination
        """
        return f"rec_{course_id}_{weekday}_{time.replace(':', '')}"

    def delete_lessons(self, lesson_id: int, delete_all_following: bool = False) -> None:
        """Löscht eine oder mehrere Unterrichtsstunden.
        
        Args:
            lesson_id: ID der zu löschenden Stunde
            delete_all_following: Bool, ob alle folgenden Stunden auch gelöscht werden sollen
        """
        try:
            # Aktuelle Stunde und deren Hash holen
            current_lesson = self.get_lesson(lesson_id)
            if not current_lesson:
                raise ValueError("Stunde nicht gefunden")
                
            if delete_all_following and current_lesson['recurring_hash']:
                # Alle folgenden Stunden mit gleichem Hash löschen
                self.execute(
                    """DELETE FROM lessons 
                    WHERE recurring_hash = ?
                    AND date >= ?""",
                    (current_lesson['recurring_hash'],
                    current_lesson['date'])
                )
            else:
                # Nur einzelne Stunde löschen
                self.execute(
                    "DELETE FROM lessons WHERE id = ?",
                    (lesson_id,)
                )
                
        except Exception as e:
            raise Exception(f"Fehler beim Löschen der Stunde(n): {str(e)}")

    def get_time_settings(self) -> dict:
        """Holt die Zeiteinstellungen aus der Datenbank.
        
        Returns:
            dict: Dictionary mit first_lesson_start, lesson_duration und breaks
                oder None wenn keine Einstellungen gefunden
        """
        try:
            # Hole Grundeinstellungen
            cursor = self.execute(
                "SELECT first_lesson_start, lesson_duration FROM timetable_settings WHERE id = 1"
            )
            settings = cursor.fetchone()
            
            if not settings:
                return None
                
            # Hole Pausen
            cursor = self.execute(
                "SELECT after_lesson, duration FROM breaks ORDER BY after_lesson"
            )
            breaks = cursor.fetchall()
            
            return {
                'first_lesson_start': settings['first_lesson_start'],
                'lesson_duration': settings['lesson_duration'],
                'breaks': [(b['after_lesson'], b['duration']) for b in breaks]
            }
            
        except Exception as e:
            print(f"Fehler beim Laden der Zeiteinstellungen: {str(e)}")
            return None


    def get_previous_lesson_homework(self, course_id: int, date: str, time: str) -> Optional[str]:
        """Holt die Hausaufgaben der vorherigen Stunde eines Kurses.
        
        Args:
            course_id: ID des Kurses
            date: Datum der aktuellen Stunde
            time: Uhrzeit der aktuellen Stunde
            
        Returns:
            Hausaufgaben der vorherigen Stunde oder None
        """
        try:
            query = """
                SELECT homework
                FROM lessons
                WHERE course_id = ? 
                AND (date < ? OR (date = ? AND time < ?))
                AND homework IS NOT NULL
                ORDER BY date DESC, time DESC
                LIMIT 1
            """
            cursor = self.execute(query, (course_id, date, date, time))
            result = cursor.fetchone()
            return result['homework'] if result else None
                
        except Exception as e:
            print(f"Fehler beim Laden der vorherigen Hausaufgaben: {str(e)}")
            return None

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


# Neue Methoden für die Verwaltung von Notensystemen:

    def add_grading_system(self, name: str, min_grade: float, max_grade: float, 
                          step_size: float, description: str = None) -> int:
        """Fügt ein neues Notensystem hinzu."""
        try:
            cursor = self.execute(
                """INSERT INTO grading_systems 
                   (name, min_grade, max_grade, step_size, description)
                   VALUES (?, ?, ?, ?, ?)""",
                (name, min_grade, max_grade, step_size, description)
            )
            return cursor.lastrowid
        except Exception as e:
            raise Exception(f"Fehler beim Hinzufügen des Notensystems: {str(e)}")

    def get_grading_system(self, system_id: int) -> dict:
        """Holt ein einzelnes Notensystem."""
        try:
            cursor = self.execute(
                "SELECT * FROM grading_systems WHERE id = ?",
                (system_id,)
            )
            result = cursor.fetchone()
            return dict(result) if result else None
        except Exception as e:
            raise Exception(f"Fehler beim Abrufen des Notensystems: {str(e)}")

    def get_all_grading_systems(self) -> list:
        """Holt alle verfügbaren Notensysteme."""
        try:
            cursor = self.execute(
                "SELECT * FROM grading_systems ORDER BY name"
            )
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            raise Exception(f"Fehler beim Abrufen der Notensysteme: {str(e)}")

    def update_grading_system(self, system_id: int, name: str, min_grade: float,
                            max_grade: float, step_size: float, description: str = None) -> None:
        """Aktualisiert ein bestehendes Notensystem."""
        try:
            self.execute(
                """UPDATE grading_systems 
                   SET name = ?, min_grade = ?, max_grade = ?, 
                       step_size = ?, description = ?
                   WHERE id = ?""",
                (name, min_grade, max_grade, step_size, description, system_id)
            )
        except Exception as e:
            raise Exception(f"Fehler beim Aktualisieren des Notensystems: {str(e)}")

    def delete_grading_system(self, system_id: int) -> None:
        """Löscht ein Notensystem."""
        try:
            self.execute(
                "DELETE FROM grading_systems WHERE id = ?",
                (system_id,)
            )
        except Exception as e:
            raise Exception(f"Fehler beim Löschen des Notensystems: {str(e)}")

    def validate_grade(self, grade: float, system_id: int) -> bool:
        """Prüft ob eine Note in einem Notensystem gültig ist."""
        try:
            system = self.get_grading_system(system_id)
            if not system:
                raise ValueError("Notensystem nicht gefunden")
                
            # Prüfe ob Note im erlaubten Bereich liegt
            if grade < system['min_grade'] or grade > system['max_grade']:
                return False
                
            # Prüfe ob Note ein gültiger Schritt ist
            steps = round((grade - system['min_grade']) / system['step_size'])
            valid_grade = system['min_grade'] + (steps * system['step_size'])
            
            # Berücksichtige Rundungsfehler
            return abs(grade - valid_grade) < 0.0001
            
        except Exception as e:
            raise Exception(f"Fehler bei der Notenvalidierung: {str(e)}")

# Neue Methoden für die Verwaltung von Templates:

    def add_assessment_template(self, name: str, subject: str, 
                              grading_system_id: int, description: str = None) -> int:
        """Fügt eine neue Bewertungstyp-Vorlage hinzu."""
        try:
            cursor = self.execute(
                """INSERT INTO assessment_type_templates 
                   (name, subject, grading_system_id, description)
                   VALUES (?, ?, ?, ?)""",
                (name, subject, grading_system_id, description)
            )
            return cursor.lastrowid
        except Exception as e:
            raise Exception(f"Fehler beim Hinzufügen der Vorlage: {str(e)}")

    def add_template_item(self, template_id: int, name: str, 
                         parent_item_id: int = None, default_weight: float = 1.0) -> int:
        """Fügt einen Bewertungstyp zu einer Vorlage hinzu."""
        try:
            cursor = self.execute(
                """INSERT INTO template_items 
                   (template_id, name, parent_item_id, default_weight)
                   VALUES (?, ?, ?, ?)""",
                (template_id, name, parent_item_id, default_weight)
            )
            return cursor.lastrowid
        except Exception as e:
            raise Exception(f"Fehler beim Hinzufügen des Vorlagenelements: {str(e)}")

    def get_assessment_template(self, template_id: int) -> dict:
        """Holt eine einzelne Bewertungstyp-Vorlage."""
        try:
            cursor = self.execute(
                """SELECT t.*, g.name as grading_system_name
                   FROM assessment_type_templates t
                   JOIN grading_systems g ON t.grading_system_id = g.id
                   WHERE t.id = ?""",
                (template_id,)
            )
            result = cursor.fetchone()
            return dict(result) if result else None
        except Exception as e:
            raise Exception(f"Fehler beim Abrufen der Vorlage: {str(e)}")

    def get_template_items(self, template_id: int) -> list:
        """Holt alle Bewertungstypen einer Vorlage hierarchisch sortiert."""
        try:
            # Zuerst die Root-Items (ohne parent)
            cursor = self.execute(
                """WITH RECURSIVE template_tree AS (
                    -- Root items (ohne parent)
                    SELECT id, name, parent_item_id, default_weight, 
                           0 as level, CAST(name as TEXT) as path
                    FROM template_items
                    WHERE template_id = ? AND parent_item_id IS NULL
                    
                    UNION ALL
                    
                    -- Child items
                    SELECT i.id, i.name, i.parent_item_id, i.default_weight,
                           tt.level + 1, 
                           tt.path || '>' || i.name
                    FROM template_items i
                    JOIN template_tree tt ON i.parent_item_id = tt.id
                )
                SELECT * FROM template_tree
                ORDER BY path;""",
                (template_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            raise Exception(f"Fehler beim Abrufen der Vorlagenelemente: {str(e)}")

    def get_templates_by_subject(self, subject: str) -> list:
        """Holt alle Vorlagen für ein bestimmtes Fach."""
        try:
            cursor = self.execute(
                """SELECT t.*, g.name as grading_system_name,
                          (SELECT COUNT(*) FROM template_items 
                           WHERE template_id = t.id) as item_count
                   FROM assessment_type_templates t
                   JOIN grading_systems g ON t.grading_system_id = g.id
                   WHERE t.subject = ?
                   ORDER BY t.name""",
                (subject,)
            )
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            raise Exception(f"Fehler beim Abrufen der Vorlagen: {str(e)}")

    def update_assessment_template(self, template_id: int, name: str, 
                                 subject: str, grading_system_id: int, 
                                 description: str = None) -> None:
        """Aktualisiert eine bestehende Vorlage."""
        try:
            self.execute(
                """UPDATE assessment_type_templates 
                   SET name = ?, subject = ?, 
                       grading_system_id = ?, description = ?
                   WHERE id = ?""",
                (name, subject, grading_system_id, description, template_id)
            )
        except Exception as e:
            raise Exception(f"Fehler beim Aktualisieren der Vorlage: {str(e)}")

    def update_template_item(self, item_id: int, name: str, 
                           parent_item_id: int = None, 
                           default_weight: float = 1.0) -> None:
        """Aktualisiert ein Vorlagenelement."""
        try:
            self.execute(
                """UPDATE template_items 
                   SET name = ?, parent_item_id = ?, default_weight = ?
                   WHERE id = ?""",
                (name, parent_item_id, default_weight, item_id)
            )
        except Exception as e:
            raise Exception(f"Fehler beim Aktualisieren des Vorlagenelements: {str(e)}")

    def delete_assessment_template(self, template_id: int) -> None:
        """Löscht eine Vorlage und alle ihre Elemente."""
        # Dank ON DELETE CASCADE werden auch alle template_items gelöscht
        try:
            self.execute(
                "DELETE FROM assessment_type_templates WHERE id = ?",
                (template_id,)
            )
        except Exception as e:
            raise Exception(f"Fehler beim Löschen der Vorlage: {str(e)}")

    def delete_template_item(self, item_id: int) -> None:
        """Löscht ein Vorlagenelement."""
        try:
            self.execute(
                "DELETE FROM template_items WHERE id = ?",
                (item_id,)
            )
        except Exception as e:
            raise Exception(f"Fehler beim Löschen des Vorlagenelements: {str(e)}")


# Neue Methoden für die Verwaltung von Assessment Types:

    def create_assessment_types_from_template(self, course_id: int, template_id: int) -> None:
        """Erstellt Bewertungstypen für einen Kurs basierend auf einer Vorlage."""
        try:
            # Hole alle Template-Items
            template_items = self.get_template_items(template_id)
            if not template_items:
                raise ValueError("Keine Template-Items gefunden")

            # Dictionary zum Speichern der ID-Zuordnungen (template_item_id -> assessment_type_id)
            id_mapping = {}

            # Items der Reihe nach einfügen (sind bereits hierarchisch sortiert)
            for item in template_items:
                # Wenn es ein Parent-Item gibt, nutze die gemappte ID
                parent_id = None
                if item['parent_item_id']:
                    parent_id = id_mapping.get(item['parent_item_id'])

                # Füge neuen Assessment Type hinzu
                new_id = self.add_assessment_type(
                    course_id=course_id,
                    name=item['name'],
                    parent_type_id=parent_id,
                    weight=item['default_weight']
                )
                
                # Speichere ID-Zuordnung
                id_mapping[item['id']] = new_id

        except Exception as e:
            raise Exception(f"Fehler beim Erstellen der Bewertungstypen: {str(e)}")

    def add_assessment_type(self, course_id: int, name: str, 
                          parent_type_id: int = None, weight: float = 1.0) -> int:
        """Fügt einen neuen Bewertungstyp hinzu."""
        try:
            cursor = self.execute(
                """INSERT INTO assessment_types 
                   (course_id, name, parent_type_id, weight)
                   VALUES (?, ?, ?, ?)""",
                (course_id, name, parent_type_id, weight)
            )
            return cursor.lastrowid
        except Exception as e:
            raise Exception(f"Fehler beim Hinzufügen des Bewertungstyps: {str(e)}")

    def get_assessment_types(self, course_id: int) -> list:
        """Holt alle Bewertungstypen eines Kurses hierarchisch sortiert."""
        try:
            cursor = self.execute(
                """WITH RECURSIVE type_tree AS (
                    -- Root types (ohne parent)
                    SELECT id, name, parent_type_id, weight, 
                           0 as level, CAST(name as TEXT) as path
                    FROM assessment_types
                    WHERE course_id = ? AND parent_type_id IS NULL
                    
                    UNION ALL
                    
                    -- Child types
                    SELECT t.id, t.name, t.parent_type_id, t.weight,
                           tt.level + 1, 
                           tt.path || '>' || t.name
                    FROM assessment_types t
                    JOIN type_tree tt ON t.parent_type_id = tt.id
                )
                SELECT * FROM type_tree
                ORDER BY path;""",
                (course_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            raise Exception(f"Fehler beim Abrufen der Bewertungstypen: {str(e)}")

    def delete_assessment_type(self, type_id: int) -> None:
        """Löscht einen Bewertungstyp und alle zugehörigen Untertypen.
        
        Args:
            type_id: ID des zu löschenden Bewertungstyps
        """
        try:
            # Prüfe ob der Typ bereits für Bewertungen verwendet wurde
            cursor = self.execute(
                "SELECT COUNT(*) as count FROM assessments WHERE assessment_type_id = ?",
                (type_id,)
            )
            result = cursor.fetchone()
            if result['count'] > 0:
                raise ValueError(
                    "Dieser Bewertungstyp wurde bereits für Noten verwendet und "
                    "kann nicht gelöscht werden."
                )

            # Lösche rekursiv alle untergeordneten Typen
            # Dies funktioniert dank ON DELETE CASCADE in der Datenbank
            self.execute(
                "DELETE FROM assessment_types WHERE id = ?",
                (type_id,)
            )
            
        except Exception as e:
            raise Exception(f"Fehler beim Löschen des Bewertungstyps: {str(e)}")

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
        """Fügt eine neue Bewertung/Note hinzu oder aktualisiert eine bestehende."""
        try:
            # Prüfe ob bereits eine Note existiert
            cursor = self.execute(
                """SELECT id FROM assessments 
                WHERE student_id = ? AND lesson_id = ?""",
                (data['student_id'], data['lesson_id'])
            )
            existing = cursor.fetchone()

            if existing:
                # Update existierende Note
                cursor = self.execute(
                    """UPDATE assessments 
                    SET grade = ?, assessment_type_id = ?, 
                        course_id = ?, date = ?, 
                        topic = ?, comment = ?, weight = ?
                    WHERE student_id = ? AND lesson_id = ?""",
                    (data['grade'], 
                    data['assessment_type_id'],
                    data['course_id'],
                    data['date'],
                    data.get('topic'),
                    data.get('comment'),  # Kommentar hinzugefügt
                    data.get('weight', 1.0),
                    data['student_id'],
                    data['lesson_id'])
                )
                return existing['id']
            else:
                # Füge neue Note hinzu
                cursor = self.execute(
                    """INSERT INTO assessments 
                    (student_id, course_id, assessment_type_id, grade,
                        date, lesson_id, topic, comment, weight)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (data['student_id'], 
                    data['course_id'],
                    data['assessment_type_id'], 
                    data['grade'],
                    data['date'],
                    data['lesson_id'],
                    data.get('topic'),
                    data.get('comment'),  # Kommentar hinzugefügt
                    data.get('weight', 1.0))
                )
                return cursor.lastrowid
        except Exception as e:
            raise Exception(f"Fehler beim Hinzufügen/Aktualisieren der Note: {str(e)}")

    def delete_assessment(self, student_id: int, lesson_id: int) -> None:
        """Löscht eine Note für einen Schüler in einer bestimmten Stunde."""
        try:
            self.execute(
                """DELETE FROM assessments 
                WHERE student_id = ? AND lesson_id = ?""",
                (student_id, lesson_id)
            )
        except Exception as e:
            raise Exception(f"Fehler beim Löschen der Note: {str(e)}")

    def get_student_assessments(self, student_id: int, course_id: int) -> list:
        """Holt alle Noten eines Schülers in einem Kurs."""
        try:
            cursor = self.execute(
                """SELECT a.*, t.name as type_name, t.weight as type_weight
                   FROM assessments a
                   JOIN assessment_types t ON a.assessment_type_id = t.id
                   WHERE a.student_id = ? AND a.course_id = ?
                   ORDER BY a.date DESC""",
                (student_id, course_id)
            )
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            raise Exception(f"Fehler beim Abrufen der Noten: {str(e)}")

    def get_lesson_assessment(self, student_id: int, lesson_id: int) -> Optional[dict]:
        """Holt die Note eines Schülers für eine bestimmte Stunde."""
        try:
            cursor = self.execute(
                """SELECT * FROM assessments 
                WHERE student_id = ? AND lesson_id = ?""",
                (student_id, lesson_id)
            )
            result = cursor.fetchone()
            return dict(result) if result else None
        except Exception as e:
            raise Exception(f"Fehler beim Laden der Note: {str(e)}")

    def get_course_assessments(self, course_id: int, assessment_type_id: int = None) -> list:
        """Holt alle Noten eines Kurses, optional gefiltert nach Bewertungstyp."""
        try:
            if assessment_type_id:
                cursor = self.execute(
                    """SELECT a.*, s.name as student_name, t.name as type_name
                       FROM assessments a
                       JOIN students s ON a.student_id = s.id
                       JOIN assessment_types t ON a.assessment_type_id = t.id
                       WHERE a.course_id = ? AND a.assessment_type_id = ?
                       ORDER BY s.name, a.date DESC""",
                    (course_id, assessment_type_id)
                )
            else:
                cursor = self.execute(
                    """SELECT a.*, s.name as student_name, t.name as type_name
                       FROM assessments a
                       JOIN students s ON a.student_id = s.id
                       JOIN assessment_types t ON a.assessment_type_id = t.id
                       WHERE a.course_id = ?
                       ORDER BY s.name, t.name, a.date DESC""",
                    (course_id,)
                )
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            raise Exception(f"Fehler beim Abrufen der Kursnoten: {str(e)}")

    def calculate_final_grade(self, student_id: int, course_id: int) -> float:
        """Berechnet die Gesamtnote eines Schülers in einem Kurs."""
        try:
        # First check if student has any grades at all
            cursor = self.execute(
                """SELECT COUNT(*) as count 
                FROM assessments 
                WHERE student_id = ? AND course_id = ?""",
                (student_id, course_id)
            )
            if cursor.fetchone()['count'] == 0:
                return None
            
            # Hole alle Bewertungstypen und deren Gewichtungen
            types = self.get_assessment_types(course_id)
            if not types:
                return None

            # Berechne gewichtete Durchschnitte für jeden Typ
            def calculate_type_average(type_id):
                cursor = self.execute(
                    """SELECT AVG(grade) as avg_grade
                       FROM assessments
                       WHERE student_id = ? AND course_id = ? 
                             AND assessment_type_id = ?""",
                    (student_id, course_id, type_id)
                )
                result = cursor.fetchone()
                return result['avg_grade'] if result else None

            # Nur Root-Level Typen (ohne parent) für Endnote
            root_types = [t for t in types if not t['parent_type_id']]
            
            weighted_sum = 0
            weight_sum = 0
            
            for type_data in root_types:
                avg = calculate_type_average(type_data['id'])
                if avg is not None:
                    weighted_sum += avg * type_data['weight']
                    weight_sum += type_data['weight']

            return round(weighted_sum / weight_sum, 2) if weight_sum > 0 else None

        except Exception as e:
            raise Exception(f"Fehler bei der Notenberechnung: {str(e)}")

    def get_student_course_grades(self, student_id: int) -> dict:
        """Holt die Gesamtnoten eines Schülers für alle seine Kurse."""
        try:
            # Hole alle Kurse des Schülers
            cursor = self.execute("""
                SELECT DISTINCT c.id, c.name
                FROM courses c
                JOIN student_courses sc ON c.id = sc.course_id
                WHERE sc.student_id = ?
                ORDER BY c.name
            """, (student_id,))
            
            courses = cursor.fetchall()
            
            # Berechne Noten für jeden Kurs
            course_grades = {}
            for course in courses:
                final_grade = self.calculate_final_grade(student_id, course['id'])
                if final_grade is not None:
                    course_grades[course['id']] = {
                        'name': course['name'],
                        'final_grade': final_grade
                    }
                    
            return course_grades
            
        except Exception as e:
            print(f"DEBUG: Error in get_student_course_grades: {str(e)}")
            raise#

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
        
        Args:
            student_id: ID des Schülers
            course_id: ID des Kurses

        Returns:
            list: Liste von Dictionaries mit Assessment Type Informationen und Noten
        """
        try:
            cursor = self.execute("""
                WITH RECURSIVE TypeHierarchy AS (
                    -- Root types
                    SELECT 
                        id, name, weight, parent_type_id,
                        name as path,
                        0 as level
                    FROM assessment_types
                    WHERE course_id = ? AND parent_type_id IS NULL
                    
                    UNION ALL
                    
                    -- Child types
                    SELECT 
                        t.id, t.name, t.weight, t.parent_type_id,
                        th.path || ' > ' || t.name,
                        th.level + 1
                    FROM assessment_types t
                    JOIN TypeHierarchy th ON t.parent_type_id = th.id
                ),
                TypeGrades AS (
                    SELECT 
                        th.*,
                        ROUND(AVG(a.grade * a.weight) / AVG(a.weight), 2) as average_grade,
                        COUNT(a.id) as grade_count
                    FROM TypeHierarchy th
                    LEFT JOIN assessments a ON th.id = a.assessment_type_id 
                        AND a.student_id = ?
                    GROUP BY th.id
                )
                SELECT * FROM TypeGrades
                ORDER BY path
            """, (course_id, student_id))
            
            return cursor.fetchall()
            
        except Exception as e:
            print(f"DEBUG: Error in get_student_assessment_type_grades: {str(e)}")
            raise
        
    def mark_student_absent(self, lesson_id: int, student_id: int) -> None:
        """Markiert einen Schüler als abwesend für eine Stunde."""
        try:
            self.execute(
                """INSERT OR REPLACE INTO student_attendance 
                (student_id, lesson_id)
                VALUES (?, ?)""",
                (student_id, lesson_id)
            )
        except Exception as e:
            raise Exception(f"Fehler beim Markieren der Abwesenheit: {str(e)}")

    def mark_student_present(self, lesson_id: int, student_id: int) -> None:
        """Löscht einen Abwesenheitseintrag (= Schüler war anwesend)."""
        try:
            self.execute(
                "DELETE FROM student_attendance WHERE lesson_id = ? AND student_id = ?",
                (lesson_id, student_id)
            )
        except Exception as e:
            raise Exception(f"Fehler beim Markieren der Anwesenheit: {str(e)}")

    def get_absent_students(self, lesson_id: int) -> List[int]:
        """Holt die IDs aller abwesenden Schüler für eine Stunde."""
        try:
            cursor = self.execute(
                "SELECT student_id FROM student_attendance WHERE lesson_id = ?",
                (lesson_id,)
            )
            return [row['student_id'] for row in cursor.fetchall()]
        except Exception as e:
            raise Exception(f"Fehler beim Laden der Abwesenheiten: {str(e)}")


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
        self.execute(
            "DELETE FROM assessment_type_templates WHERE id = ?",
            (template_id,)
        )