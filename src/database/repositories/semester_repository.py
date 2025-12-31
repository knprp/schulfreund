# src/database/repositories/semester_repository.py

from typing import List, Dict, Any, Optional
from .base_repository import BaseRepository


class SemesterRepository(BaseRepository):
    """Repository für Semester-Operationen."""
    
    def save_current(self, start_date: str, end_date: str) -> None:
        """Speichert die aktuellen Semesterdaten.
        
        Args:
            start_date: Startdatum im Format "YYYY-MM-DD"
            end_date: Enddatum im Format "YYYY-MM-DD"
        """
        self.execute(
            """INSERT OR REPLACE INTO settings 
               (id, semester_start, semester_end)
               VALUES (1, ?, ?)""",
            (start_date, end_date)
        )
    
    def get_current(self) -> Optional[Dict[str, Any]]:
        """Holt die aktuellen Semesterdaten.
        
        Returns:
            Dictionary mit semester_start und semester_end oder None
        """
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
    
    def save_to_history(self, start_date: str, end_date: str, 
                       name: Optional[str] = None, notes: Optional[str] = None) -> int:
        """Speichert ein Halbjahr in der Historie.
        
        Args:
            start_date: Startdatum im Format "YYYY-MM-DD"
            end_date: Enddatum im Format "YYYY-MM-DD"
            name: Optional, benutzerdefinierter Name
            notes: Optional, Anmerkungen
            
        Returns:
            ID des neu erstellten Semester-Eintrags
        """
        cursor = self.execute(
            """INSERT INTO semester_history (start_date, end_date, name, notes)
            VALUES (?, ?, ?, ?)""",
            (start_date, end_date, name, notes)
        )
        return cursor.lastrowid
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Holt alle gespeicherten Halbjahre.
        
        Returns:
            Liste von Dictionaries mit Semesterdaten, sortiert nach Startdatum (neueste zuerst)
        """
        cursor = self.execute(
            """SELECT * FROM semester_history 
            ORDER BY start_date DESC"""
        )
        return self._dicts_from_rows(cursor.fetchall())
    
    def get_by_date(self, date: str) -> Optional[Dict[str, Any]]:
        """Findet das Halbjahr zu einem bestimmten Datum.
        
        Args:
            date: Datum im Format "YYYY-MM-DD"
            
        Returns:
            Dictionary mit Semesterdaten oder None
        """
        cursor = self.execute(
            """SELECT * FROM semester_history 
            WHERE start_date <= ? AND end_date >= ?
            ORDER BY start_date DESC LIMIT 1""",
            (date, date)
        )
        row = cursor.fetchone()
        return self._dict_from_row(row)
    
    def delete_from_history(self, semester_id: int) -> None:
        """Löscht ein Halbjahr aus der Historie.
        
        Args:
            semester_id: ID des zu löschenden Semesters
        """
        self.execute(
            "DELETE FROM semester_history WHERE id = ?",
            (semester_id,)
        )
