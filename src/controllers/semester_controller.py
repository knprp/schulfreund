# src/controllers/semester_controller.py

"""
Controller für Semester-Operationen.

Kapselt Business-Logik für Semester-Verwaltung.
"""

from typing import Dict, Any, Optional, List
from .base_controller import BaseController


class SemesterController(BaseController):
    """Controller für Semester-Operationen."""
    
    def get_current_semester(self) -> Optional[Dict[str, Any]]:
        """Holt das aktuelle Semester.
        
        Returns:
            Dictionary mit Semester-Daten oder None
        """
        return self.semester_repo.get_current()
    
    def get_semester_dates(self) -> Optional[Dict[str, Any]]:
        """Holt die aktuellen Semesterdaten (Kompatibilitätsmethode).
        
        Returns:
            Dictionary mit semester_start und semester_end oder None
        """
        # get_current() gibt bereits semester_start und semester_end zurück
        return self.semester_repo.get_current()
    
    def get_semester_by_date(self, date: str) -> Optional[Dict[str, Any]]:
        """Findet das Semester zu einem bestimmten Datum.
        
        Args:
            date: Datum im Format 'YYYY-MM-DD'
            
        Returns:
            Dictionary mit Semester-Daten oder None
        """
        return self.semester_repo.get_by_date(date)
    
    def save_current_semester(self, start_date: str, end_date: str) -> None:
        """Speichert das aktuelle Semester.
        
        Args:
            start_date: Startdatum im Format 'YYYY-MM-DD'
            end_date: Enddatum im Format 'YYYY-MM-DD'
        """
        self.semester_repo.save_current(start_date, end_date)
    
    def get_semester_history(self) -> List[Dict[str, Any]]:
        """Holt die Semester-Historie.
        
        Returns:
            Liste von Dictionaries mit Semester-Daten
        """
        return self.semester_repo.get_history()
