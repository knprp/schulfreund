# src/controllers/lesson_controller.py

"""
Controller für Unterrichtsstunden-Operationen.

Kapselt Business-Logik und Datenaggregation für Stunden-bezogene Operationen.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from .base_controller import BaseController


class LessonController(BaseController):
    """Controller für Unterrichtsstunden-Operationen."""
    
    def get_lesson(self, lesson_id: int) -> Optional[Dict[str, Any]]:
        """Holt eine Stunde anhand ihrer ID.
        
        Args:
            lesson_id: ID der Stunde
            
        Returns:
            Dictionary mit Stundendaten oder None
        """
        return self.lesson_repo.get_by_id(lesson_id)
    
    def get_lessons_by_date(self, date: str) -> List[Dict[str, Any]]:
        """Holt alle Stunden für ein bestimmtes Datum.
        
        Args:
            date: Datum im Format 'YYYY-MM-DD'
            
        Returns:
            Liste von Dictionaries mit Stundendaten
        """
        return self.lesson_repo.get_by_date(date)
    
    def create_lesson(self, course_id: int, date: str, time: str,
                     topic: Optional[str] = None, homework: Optional[str] = None,
                     duration: Optional[int] = None, status: str = "normal",
                     status_note: Optional[str] = None) -> int:
        """Erstellt eine neue Stunde.
        
        Args:
            course_id: ID des Kurses
            date: Datum im Format 'YYYY-MM-DD'
            time: Uhrzeit im Format 'HH:MM'
            topic: Optional, Thema
            homework: Optional, Hausaufgaben
            duration: Optional, Dauer in Minuten
            status: Status ('normal', 'cancelled', 'moved', 'substituted')
            status_note: Optional, Notiz zum Status
            
        Returns:
            ID der neu erstellten Stunde
        """
        return self.lesson_repo.add(course_id, date, time, topic, homework, duration, status, status_note)
    
    def update_lesson(self, lesson_id: int, data: Dict[str, Any], 
                     update_all_following: bool = False) -> List[int]:
        """Aktualisiert eine oder mehrere Unterrichtsstunden.
        
        Args:
            lesson_id: ID der Stunde
            data: Dictionary mit zu aktualisierenden Daten
            update_all_following: Wenn True, werden alle folgenden wiederkehrenden Stunden aktualisiert
            
        Returns:
            Liste von IDs der aktualisierten Stunden
        """
        return self.lesson_repo.update(lesson_id, data, update_all_following)
    
    def delete_lesson(self, lesson_id: int) -> None:
        """Löscht eine Stunde.
        
        Args:
            lesson_id: ID der zu löschenden Stunde
        """
        self.lesson_repo.delete(lesson_id)
    
    def add_competency_to_lesson(self, lesson_id: int, competency_id: int) -> None:
        """Fügt eine Kompetenz zu einer Stunde hinzu.
        
        Args:
            lesson_id: ID der Stunde
            competency_id: ID der Kompetenz
        """
        self.lesson_repo.add_competency(lesson_id, competency_id)
    
    def get_lessons_by_date(self, date: str) -> List[Dict[str, Any]]:
        """Holt alle Stunden für ein bestimmtes Datum.
        
        Args:
            date: Datum im Format 'YYYY-MM-DD'
            
        Returns:
            Liste von Dictionaries mit Stundendaten
        """
        return self.lesson_repo.get_by_date(date)
    
    def add_lesson(self, data: Dict[str, Any]) -> int or List[int]:
        """Fügt eine neue Unterrichtsstunde hinzu (unterstützt wiederkehrende Stunden).
        
        Args:
            data: Dictionary mit Stundendaten
            
        Returns:
            ID der erstellten Stunde oder Liste von IDs bei wiederkehrenden Stunden
        """
        return self.lesson_repo.add(data)
    
    def get_next_lesson_by_course(self, date: str) -> List[Dict[str, Any]]:
        """Holt für jeden Kurs die nächste anstehende Stunde nach einem Datum.
        
        Args:
            date: Datum im Format 'YYYY-MM-DD'
            
        Returns:
            Liste von Dictionaries mit Stundendaten
        """
        return self.lesson_repo.get_next_by_course(date)
    
    def get_previous_homework(self, course_id: int, date: str, time: str) -> Optional[str]:
        """Holt die Hausaufgaben der vorherigen Stunde eines Kurses.
        
        Args:
            course_id: ID des Kurses
            date: Datum im Format 'YYYY-MM-DD'
            time: Uhrzeit im Format 'HH:MM'
            
        Returns:
            Hausaufgaben-Text oder None
        """
        return self.lesson_repo.get_previous_homework(course_id, date, time)
    
    def update_lesson(self, lesson_id: int, data: Dict[str, Any], 
                     update_all_following: bool = False) -> List[int]:
        """Aktualisiert eine oder mehrere Unterrichtsstunden.
        
        Args:
            lesson_id: ID der Stunde
            data: Dictionary mit zu aktualisierenden Daten
            update_all_following: Wenn True, werden alle folgenden wiederkehrenden Stunden aktualisiert
            
        Returns:
            Liste von IDs der aktualisierten Stunden
        """
        return self.lesson_repo.update(lesson_id, data, update_all_following)
    
    def delete_lessons(self, lesson_id: int, delete_all: bool = False) -> None:
        """Löscht eine oder mehrere Unterrichtsstunden.
        
        Args:
            lesson_id: ID der Stunde
            delete_all: Wenn True, werden alle wiederkehrenden Stunden gelöscht
        """
        self.lesson_repo.delete(lesson_id, delete_all)
    
    def get_competencies_for_lesson(self, lesson_id: int) -> List[Dict[str, Any]]:
        """Holt alle Kompetenzen einer Stunde.
        
        Args:
            lesson_id: ID der Stunde
            
        Returns:
            Liste von Dictionaries mit Kompetenzdaten
        """
        # Hole competency_ids über die JOIN-Tabelle
        cursor = self.db.execute(
            """SELECT competency_id FROM lesson_competencies
            WHERE lesson_id = ?""",
            (lesson_id,)
        )
        competency_ids = [row['competency_id'] for row in cursor.fetchall()]
        
        # Hole die Kompetenz-Details
        competencies = []
        for comp_id in competency_ids:
            comp = self.competency_repo.get_by_id(comp_id)
            if comp:
                competencies.append(comp)
        
        return competencies
    
    def remove_all_competencies_from_lesson(self, lesson_id: int) -> None:
        """Entfernt alle Kompetenzen von einer Stunde.
        
        Args:
            lesson_id: ID der Stunde
        """
        self.db.execute(
            "DELETE FROM lesson_competencies WHERE lesson_id = ?",
            (lesson_id,)
        )
    
    def get_all_lessons(self) -> List[Dict[str, Any]]:
        """Holt alle Unterrichtsstunden.
        
        Returns:
            Liste von Dictionaries mit Stundendaten
        """
        return self.lesson_repo.get_all()
