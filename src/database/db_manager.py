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
        except sqlite3.Error as e:
            raise Exception(f"Datenbankverbindung fehlgeschlagen: {e}")

    def setup_tables(self) -> None:
        """Erstellt alle notwendigen Tabellen falls sie nicht existieren."""
        try:
            cursor = self.conn.cursor()
            
            # Studenten Tabelle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
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
            
            
            # Noten Tabelle mit Foreign Keys
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS grades (
                    id INTEGER PRIMARY KEY,
                    student_id INTEGER NOT NULL,
                    lesson_id INTEGER NOT NULL,
                    competency_id INTEGER NOT NULL,
                    grade INTEGER NOT NULL,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
                    FOREIGN KEY (lesson_id) REFERENCES lessons (id) ON DELETE CASCADE,
                    FOREIGN KEY (competency_id) REFERENCES competencies (id) ON DELETE CASCADE
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Optionale Schüler-Kurs Zuordnung
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS student_courses (
                    student_id INTEGER,
                    course_id INTEGER,
                    start_date TEXT NOT NULL,  -- Format: YYYY-MM-DD
                    end_date TEXT NOT NULL,    -- Format: YYYY-MM-DD
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (student_id, course_id, start_date),
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
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
                    recurring_hash TEXT,
                    lesson_number INTEGER,
                    duration INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
                )
            ''')

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

            self.conn.commit()               
        except sqlite3.Error as e:
            raise Exception(f"Fehler beim Erstellen der Tabellen: {e}")

                                      

                   # Indizes für bessere Performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_grades_student ON grades(student_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_grades_lesson ON grades(lesson_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_grades_competency ON grades(competency_id)')
  

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
                "SELECT id, name FROM students ORDER BY name"
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
                    
                # Hash generieren - hier die wichtige Änderung
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
                            data['date'],
                            data['time'],
                            data['subject'],
                            data.get('topic', ''),
                            rec_hash,
                            data.get('duration', 1))  # Duration hinzugefügt
                        )
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
                            data.get('duration', 1))  # Duration hinzugefügt
                        )
                    return cursor.lastrowid

        except Exception as e:
            raise Exception(f"Fehler beim Hinzufügen der Unterrichtsstunde: {str(e)}")

    def get_lessons_by_date(self, date: str) -> List[Dict[str, Any]]:
        """Holt alle Unterrichtsstunden für ein bestimmtes Datum."""
        cursor = self.execute(
            "SELECT * FROM lessons WHERE date = ? ORDER BY time",
            (date,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_all_lessons(self) -> List[Dict[str, Any]]:
        """Holt alle Unterrichtsstunden."""
        cursor = self.execute(
            "SELECT * FROM lessons ORDER BY date, time"
        )
        return [dict(row) for row in cursor.fetchall()]

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
    def add_grade(self, student_id: int, lesson_id: int, 
                 competency_id: int, grade: int, comment: str = "") -> int:
        """Fügt eine neue Note hinzu."""
        cursor = self.execute(
            """INSERT INTO grades 
               (student_id, lesson_id, competency_id, grade, comment)
               VALUES (?, ?, ?, ?, ?)""",
            (student_id, lesson_id, competency_id, grade, comment)
        )
        return cursor.lastrowid

    def get_grades_by_student(self, student_id: int) -> List[Dict[str, Any]]:
        """Holt alle Noten eines Schülers mit zugehörigen Informationen."""
        cursor = self.execute(
            """SELECT g.*, l.subject, l.date, c.area, c.description
               FROM grades g
               JOIN lessons l ON g.lesson_id = l.id
               JOIN competencies c ON g.competency_id = c.id
               WHERE g.student_id = ?
               ORDER BY l.date DESC""",
            (student_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

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

    def add_grade(self, data: dict) -> int:
        """Fügt eine neue Note hinzu mit erweiterten Eigenschaften."""
        try:
            cursor = self.execute('''
                INSERT INTO grades (
                    student_id, lesson_id, competency_id, 
                    grade, grade_type, weight, comment
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['student_id'], 
                data['lesson_id'],
                data['competency_id'],
                data['grade'],
                data.get('grade_type', 'regular'),
                data.get('weight', 1.0),
                data.get('comment', '')
            ))
            return cursor.lastrowid
        except sqlite3.Error as e:
            raise Exception(f"Fehler beim Hinzufügen der Note: {e}")

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

    def get_grade_statistics(self, student_id: int) -> dict:
        """Berechnet Notenstatistiken für einen Schüler."""
        try:
            cursor = self.execute('''
                SELECT 
                    l.subject,
                    COUNT(*) as count,
                    AVG(g.grade * g.weight) as weighted_average,
                    MIN(g.grade) as best_grade,
                    MAX(g.grade) as worst_grade
                FROM grades g
                JOIN lessons l ON g.lesson_id = l.id
                WHERE g.student_id = ?
                GROUP BY l.subject
            ''', (student_id,))
            
            return {row['subject']: dict(row) for row in cursor.fetchall()}
        except sqlite3.Error as e:
            raise Exception(f"Fehler beim Berechnen der Statistiken: {e}")

    def update_grade(self, grade_id: int, data: dict) -> None:
        """Aktualisiert eine bestehende Note."""
        try:
            fields = []
            values = []
            for key, value in data.items():
                if key not in ['id', 'created_at']:
                    fields.append(f"{key} = ?")
                    values.append(value)
            
            values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))  # updated_at
            values.append(grade_id)  # WHERE id = ?
            
            query = f'''
                UPDATE grades 
                SET {', '.join(fields)}, updated_at = ?
                WHERE id = ?
            '''
            
            self.execute(query, tuple(values))
        except sqlite3.Error as e:
            raise Exception(f"Fehler beim Aktualisieren der Note: {e}")

    def get_grade(self, grade_id: int) -> dict:
        """Holt eine einzelne Note mit allen Details."""
        try:
            cursor = self.execute('''
                SELECT 
                    g.*,
                    l.date as lesson_date,
                    l.subject,
                    c.area as competency_area,
                    c.description as competency_description
                FROM grades g
                JOIN lessons l ON g.lesson_id = l.id
                JOIN competencies c ON g.competency_id = c.id
                WHERE g.id = ?
            ''', (grade_id,))
            
            result = cursor.fetchone()
            return dict(result) if result else None
        except sqlite3.Error as e:
            raise Exception(f"Fehler beim Abrufen der Note: {e}")

    def add_lesson_competency(self, lesson_id: int, competency_id: int):
        """Fügt eine Verbindung zwischen Unterrichtsstunde und Kompetenz hinzu."""
        try:
            self.execute(
                "INSERT INTO lesson_competencies (lesson_id, competency_id) VALUES (?, ?)",
                (lesson_id, competency_id)
            )
        except sqlite3.Error as e:
            raise Exception(f"Fehler beim Verknüpfen von Stunde und Kompetenz: {e}")

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

    def get_lessons_by_date(self, date: str) -> List[Dict[str, Any]]:
        """Holt alle Unterrichtsstunden für ein bestimmtes Datum."""
        cursor = self.execute(
            """SELECT l.*, c.name as course_name
            FROM lessons l
            JOIN courses c ON l.course_id = c.id
            WHERE l.date = ? 
            ORDER BY l.time""",
            (date,)
        )
        return [dict(row) for row in cursor.fetchall()]

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
        print(f"DEBUG - generate_recurring_hash - time type: {type(time)}, value: {time}")
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