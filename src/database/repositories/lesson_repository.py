# src/database/repositories/lesson_repository.py

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .base_repository import BaseRepository


class LessonRepository(BaseRepository):
    """Repository für Unterrichtsstunden-Operationen."""
    
    def add(self, data: dict) -> int or list:
        """Fügt eine neue Unterrichtsstunde hinzu.
        
        Unterstützt sowohl einzelne Stunden als auch wiederkehrende Stunden.
        
        Args:
            data: Dictionary mit Stundendaten:
                - course_id: ID des Kurses (erforderlich)
                - date: Datum im Format "YYYY-MM-DD"
                - time: Uhrzeit im Format "HH:MM"
                - subject: Fach
                - topic: Optional, Thema
                - homework: Optional, Hausaufgaben
                - duration: Optional, Dauer in Stunden (Standard: 1)
                - status: Optional, Status (Standard: 'normal')
                - status_note: Optional, Status-Notiz
                - moved_to_lesson_id: Optional, ID der verschobenen Stunde
                - is_recurring: Optional, bool für wiederkehrende Stunden
                
        Returns:
            ID der erstellten Stunde oder Liste von IDs bei wiederkehrenden Stunden
        """
        if not data.get('course_id'):
            raise ValueError("Eine Unterrichtsstunde muss einem Kurs zugeordnet sein")
        
        if data.get('is_recurring'):
            # Semesterdaten holen (benötigt SemesterRepository)
            from .semester_repository import SemesterRepository
            semester_repo = SemesterRepository(self.db)
            semester = semester_repo.get_current()
            if not semester:
                raise ValueError("Kein aktives Halbjahr gefunden")
            
            # Wochentag bestimmen
            start_date = datetime.strptime(data['date'], "%Y-%m-%d")
            weekday = start_date.isoweekday()
            
            # Hash generieren
            time_str = data['time'] if isinstance(data['time'], str) else data['time'][0]
            rec_hash = self._generate_recurring_hash(
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
                        (course_id, date, time, subject, topic, homework, recurring_hash, 
                         duration, status, status_note, moved_to_lesson_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (data['course_id'],
                         current_date.strftime("%Y-%m-%d"),
                         data['time'],
                         data['subject'],
                         data.get('topic', ''),
                         data.get('homework'),
                         rec_hash,
                         data.get('duration', 1),
                         data.get('status', 'normal'),
                         data.get('status_note'),
                         data.get('moved_to_lesson_id'))
                    )
                    lesson_ids.append(cursor.lastrowid)
                current_date += timedelta(days=1)
            
            # Status für Feiertage aktualisieren
            from .holiday_repository import HolidayRepository
            holiday_repo = HolidayRepository(self.db)
            holiday_repo.update_lesson_status_for_holidays()
            
            return lesson_ids
        else:
            # Normale einzelne Unterrichtsstunde
            cursor = self.execute(
                """INSERT INTO lessons
                (course_id, date, time, subject, topic, homework, duration,
                status, status_note, moved_to_lesson_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (data['course_id'],
                 data['date'],
                 data['time'],
                 data['subject'],
                 data.get('topic', ''),
                 data.get('homework'),
                 data.get('duration', 1),
                 data.get('status', 'normal'),
                 data.get('status_note'),
                 data.get('moved_to_lesson_id'))
            )
            return cursor.lastrowid
    
    def get_by_id(self, lesson_id: int) -> Optional[Dict[str, Any]]:
        """Holt eine einzelne Unterrichtsstunde mit Kursinformationen.
        
        Args:
            lesson_id: ID der Stunde
            
        Returns:
            Dictionary mit Stundendaten oder None
        """
        cursor = self.execute(
            """SELECT l.*, c.name as course_name, c.subject as course_subject
            FROM lessons l
            JOIN courses c ON l.course_id = c.id
            WHERE l.id = ?""",
            (lesson_id,)
        )
        row = cursor.fetchone()
        return self._dict_from_row(row)
    
    def get_by_date(self, date: str) -> List[Dict[str, Any]]:
        """Holt alle Unterrichtsstunden für ein bestimmtes Datum.
        
        Args:
            date: Datum im Format "YYYY-MM-DD"
            
        Returns:
            Liste von Dictionaries mit Stundendaten inkl. Kursinformationen
        """
        query = """
            SELECT 
                l.*,
                c.name as course_name,
                c.color as course_color
            FROM lessons l
            JOIN courses c ON l.course_id = c.id
            WHERE l.date = ?
            ORDER BY l.time
        """
        cursor = self.execute(query, (date,))
        return self._dicts_from_rows(cursor.fetchall())
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Holt alle Unterrichtsstunden.
        
        Returns:
            Liste von Dictionaries mit Stundendaten, sortiert nach Datum und Zeit
        """
        cursor = self.execute(
            "SELECT * FROM lessons ORDER BY date, time"
        )
        return self._dicts_from_rows(cursor.fetchall())
    
    def get_next_by_course(self, date: str) -> List[Dict[str, Any]]:
        """Holt für jeden Kurs die nächste anstehende Stunde nach einem Datum.
        
        Args:
            date: Startdatum im Format "YYYY-MM-DD"
            
        Returns:
            Liste von Dictionaries mit den nächsten Stunden pro Kurs
        """
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
        all_lessons = self._dicts_from_rows(cursor.fetchall())
        
        # Dictionary für die nächsten Stunden pro Kurs
        next_lessons = {}
        current_time = datetime.now()
        current_time_str = current_time.strftime("%H:%M")
        
        # Hole Zeiteinstellungen für Stundenlänge
        from .settings_repository import SettingsRepository
        settings_repo = SettingsRepository(self.db)
        settings = settings_repo.get_time_settings()
        lesson_duration = 45  # Standard-Stundenlänge in Minuten
        if settings and 'lesson_duration' in settings:
            lesson_duration = settings['lesson_duration']
        
        for lesson in all_lessons:
            course_id = lesson['course_id']
            if course_id in next_lessons:
                continue
            
            # Berechne Endzeit der Stunde
            lesson_time = datetime.strptime(lesson['time'], "%H:%M")
            lesson_end = (lesson_time + timedelta(
                minutes=lesson_duration * lesson.get('duration', 1)
            )).time()
            
            # Überspringe Stunden vom aktuellen Tag die schon vorbei sind
            if (lesson['date'] == date and 
                lesson_end.strftime("%H:%M") <= current_time_str):
                continue
            
            next_lessons[course_id] = lesson
        
        return list(next_lessons.values())
    
    def update(self, lesson_id: int, data: dict, update_all_following: bool = False) -> List[int]:
        """Aktualisiert eine oder mehrere Unterrichtsstunden.
        
        Args:
            lesson_id: ID der zu ändernden Stunde
            data: Dictionary mit den neuen Daten
            update_all_following: Wenn True, werden alle folgenden Stunden mit 
                                gleichem recurring_hash auch geändert
                
        Returns:
            Liste der IDs aller geänderten Stunden
        """
        # Aktuelle Stunde und deren Hash holen
        current_lesson = self.get_by_id(lesson_id)
        if not current_lesson:
            raise ValueError("Stunde nicht gefunden")
        
        if update_all_following and current_lesson.get('recurring_hash'):
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
    
    def delete(self, lesson_id: int, delete_all_following: bool = False) -> None:
        """Löscht eine oder mehrere Unterrichtsstunden.
        
        Args:
            lesson_id: ID der zu löschenden Stunde
            delete_all_following: Wenn True, werden alle folgenden Stunden mit 
                                 gleichem recurring_hash auch gelöscht
        """
        # Aktuelle Stunde und deren Hash holen
        current_lesson = self.get_by_id(lesson_id)
        if not current_lesson:
            raise ValueError("Stunde nicht gefunden")
        
        if delete_all_following and current_lesson.get('recurring_hash'):
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
    
    def get_previous_homework(self, course_id: int, date: str, time: str) -> Optional[str]:
        """Holt die Hausaufgaben der vorherigen Stunde eines Kurses.
        
        Args:
            course_id: ID des Kurses
            date: Datum der aktuellen Stunde
            time: Uhrzeit der aktuellen Stunde
            
        Returns:
            Hausaufgaben der vorherigen Stunde oder None
        """
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
    
    def add_competency(self, lesson_id: int, competency_id: int) -> None:
        """Fügt eine Verknüpfung zwischen Unterrichtsstunde und Kompetenz hinzu.
        
        Args:
            lesson_id: ID der Stunde
            competency_id: ID der Kompetenz
        """
        try:
            self.execute(
                "INSERT INTO lesson_competencies (lesson_id, competency_id) VALUES (?, ?)",
                (lesson_id, competency_id)
            )
        except Exception:
            # Falls die Verknüpfung bereits existiert, ignorieren wir den Fehler
            pass
    
    def _generate_recurring_hash(self, course_id: int, weekday: int, time: str) -> str:
        """Generiert einen Hash für wiederkehrende Stunden.
        
        Args:
            course_id: ID des Kurses
            weekday: Wochentag als int (1=Montag, 7=Sonntag)
            time: Uhrzeit im Format "HH:MM"
            
        Returns:
            Hash-String für diese Kombination
        """
        return f"rec_{course_id}_{weekday}_{time.replace(':', '')}"
