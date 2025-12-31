# src/database/repositories/settings_repository.py

from typing import Dict, Any, Optional, List, Tuple
from .base_repository import BaseRepository


class SettingsRepository(BaseRepository):
    """Repository für Einstellungs-Operationen."""
    
    def get_time_settings(self) -> Optional[Dict[str, Any]]:
        """Holt die Zeiteinstellungen aus der Datenbank.
        
        Returns:
            Dictionary mit first_lesson_start, lesson_duration und breaks
            oder None wenn keine Einstellungen gefunden
        """
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
    
    def update_time_settings(self, first_lesson_start: str, lesson_duration: int) -> None:
        """Aktualisiert die Zeiteinstellungen.
        
        Args:
            first_lesson_start: Startzeit der ersten Stunde (z.B. "08:00")
            lesson_duration: Dauer einer Stunde in Minuten
        """
        self.execute(
            """UPDATE timetable_settings 
            SET first_lesson_start = ?, lesson_duration = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1""",
            (first_lesson_start, lesson_duration)
        )
    
    def update_breaks(self, breaks: List[Tuple[int, int]]) -> None:
        """Aktualisiert die Pausen-Konfiguration.
        
        Args:
            breaks: Liste von Tupeln (after_lesson, duration)
        """
        # Alte Pausen löschen
        self.execute("DELETE FROM breaks")
        
        # Neue Pausen einfügen
        if breaks:
            self.execute(
                "INSERT INTO breaks (after_lesson, duration) VALUES (?, ?)",
                breaks[0]
            )
            if len(breaks) > 1:
                cursor = self.db.conn.cursor()
                cursor.executemany(
                    "INSERT INTO breaks (after_lesson, duration) VALUES (?, ?)",
                    breaks[1:]
                )
                self.db.conn.commit()
