# src/controllers/settings_controller.py

"""
Controller für Einstellungs-Operationen.

Kapselt Business-Logik für Einstellungen wie Zeiteinstellungen, Semester, etc.
"""

from typing import Dict, Any, Optional, List, Tuple
from .base_controller import BaseController


class SettingsController(BaseController):
    """Controller für Einstellungs-Operationen."""
    
    def get_time_settings(self) -> Optional[Dict[str, Any]]:
        """Holt die Zeiteinstellungen aus der Datenbank.
        
        Returns:
            Dictionary mit first_lesson_start, lesson_duration und breaks
            oder None wenn keine Einstellungen gefunden
        """
        return self.settings_repo.get_time_settings()
    
    def update_time_settings(self, first_lesson_start: str, lesson_duration: int) -> None:
        """Aktualisiert die Zeiteinstellungen.
        
        Args:
            first_lesson_start: Startzeit der ersten Stunde (z.B. "08:00")
            lesson_duration: Dauer einer Stunde in Minuten
        """
        self.settings_repo.update_time_settings(first_lesson_start, lesson_duration)
    
    def get_breaks(self) -> List[Dict[str, Any]]:
        """Holt alle Pausen.
        
        Returns:
            Liste von Dictionaries mit Pausendaten, sortiert nach after_lesson
        """
        cursor = self.db.execute(
            "SELECT after_lesson, duration FROM breaks ORDER BY after_lesson"
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def update_breaks(self, breaks: List[Dict[str, int]]) -> None:
        """Aktualisiert die Pausen-Konfiguration.
        
        Args:
            breaks: Liste von Dictionaries mit 'after_lesson' und 'duration'
        """
        # Konvertiere zu Tupeln für das Repository
        breaks_tuples = [(b['after_lesson'], b['duration']) for b in breaks]
        self.settings_repo.update_breaks(breaks_tuples)
