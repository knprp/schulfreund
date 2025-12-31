# src/database/repositories/holiday_repository.py

from typing import List, Dict, Any
from .base_repository import BaseRepository


class HolidayRepository(BaseRepository):
    """Repository für Feiertags-Operationen."""
    
    def add_public(self, date: str, name: str, type: str, state: str, year: int) -> int:
        """Fügt einen neuen öffentlichen Feiertag/Ferientag hinzu.
        
        Args:
            date: Datum im Format "YYYY-MM-DD"
            name: Name des Feiertags
            type: Typ ('holiday' oder 'vacation_day')
            state: Bundesland (z.B. "NW")
            year: Jahr
            
        Returns:
            ID des neu erstellten Feiertags
        """
        cursor = self.execute(
            """INSERT INTO public_holidays 
            (date, name, type, state, year) 
            VALUES (?, ?, ?, ?, ?)""",
            (date, name, type, state, year)
        )
        return cursor.lastrowid
    
    def add_school(self, date: str, name: str, description: str = None) -> int:
        """Fügt einen schulspezifischen freien Tag hinzu.
        
        Args:
            date: Datum im Format "YYYY-MM-DD"
            name: Name des freien Tages
            description: Optional, Beschreibung
            
        Returns:
            ID des neu erstellten freien Tages
        """
        cursor = self.execute(
            """INSERT INTO school_holidays 
            (date, name, description)
            VALUES (?, ?, ?)""",
            (date, name, description)
        )
        return cursor.lastrowid
    
    def delete_public(self, holiday_id: int) -> None:
        """Löscht einen öffentlichen Feiertag/Ferientag.
        
        Args:
            holiday_id: ID des Feiertags
        """
        self.execute(
            "DELETE FROM public_holidays WHERE id = ?",
            (holiday_id,)
        )
    
    def delete_school(self, holiday_id: int) -> None:
        """Löscht einen schulspezifischen freien Tag.
        
        Args:
            holiday_id: ID des freien Tages
        """
        self.execute(
            "DELETE FROM school_holidays WHERE id = ?",
            (holiday_id,)
        )
    
    def get_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Holt alle Feiertage und freien Tage in einem Zeitraum.
        
        Args:
            start_date: Startdatum im Format "YYYY-MM-DD"
            end_date: Enddatum im Format "YYYY-MM-DD"
            
        Returns:
            Liste von Dictionaries mit Feiertagsdaten, sortiert nach Datum
        """
        # Erst die öffentlichen Feiertage/Ferien
        cursor = self.execute(
            """SELECT date, name, type, 'public' as source
            FROM public_holidays 
            WHERE date BETWEEN ? AND ?""",
            (start_date, end_date)
        )
        holidays = self._dicts_from_rows(cursor.fetchall())
        
        # Dann die schulspezifischen
        cursor = self.execute(
            """SELECT date, name, 'school' as type, 'school' as source
            FROM school_holidays 
            WHERE date BETWEEN ? AND ?""",
            (start_date, end_date)
        )
        holidays.extend(self._dicts_from_rows(cursor.fetchall()))
        
        # Sortiert nach Datum zurückgeben
        return sorted(holidays, key=lambda x: x['date'])
    
    def clear_public_by_year(self, year: int, state: str) -> None:
        """Löscht alle öffentlichen Feiertage eines Jahres/Bundeslandes.
        
        Args:
            year: Jahr
            state: Bundesland
        """
        self.execute(
            """DELETE FROM public_holidays 
            WHERE year = ? AND state = ?""",
            (year, state)
        )
    
    def get_school_holidays(self) -> List[Dict[str, Any]]:
        """Holt alle schulspezifischen freien Tage.
        
        Returns:
            Liste von Dictionaries mit freien Tagen, sortiert nach Datum
        """
        cursor = self.execute(
            """SELECT * FROM school_holidays 
            ORDER BY date"""
        )
        return self._dicts_from_rows(cursor.fetchall())
    
    def get_public_by_year(self, year: int, state: str) -> List[Dict[str, Any]]:
        """Holt alle öffentlichen Feiertage/Ferien eines Jahres.
        
        Args:
            year: Jahr
            state: Bundesland
            
        Returns:
            Liste von Dictionaries mit Feiertagsdaten, sortiert nach Datum
        """
        cursor = self.execute(
            """SELECT * FROM public_holidays 
            WHERE year = ? AND state = ?
            ORDER BY date""",
            (year, state)
        )
        return self._dicts_from_rows(cursor.fetchall())
    
    def update_lesson_status_for_holidays(self) -> None:
        """Aktualisiert den Status von Stunden, die in Ferien/an Feiertagen liegen."""
        # Hole alle Stunden
        cursor = self.execute(
            "SELECT id, date FROM lessons"
        )
        lessons = cursor.fetchall()
        
        for lesson in lessons:
            # Prüfe ob das Datum ein Feiertag/Ferientag ist
            cursor = self.execute(
                """SELECT type, name FROM public_holidays 
                WHERE date = ?""",
                (lesson['date'],)
            )
            holiday = cursor.fetchone()
            
            if holiday:
                status_note = f"Entfällt wegen {'Feiertag' if holiday['type'] == 'holiday' else 'Ferien'}: {holiday['name']}"
                # Update den Status
                self.execute(
                    """UPDATE lessons 
                    SET status = 'cancelled',
                        status_note = ?
                    WHERE id = ?""",
                    (status_note, lesson['id'])
                )
