# src/database/repositories/grading_system_repository.py

from typing import List, Dict, Any, Optional
from .base_repository import BaseRepository


class GradingSystemRepository(BaseRepository):
    """Repository für Notensystem-Operationen."""
    
    def add(self, name: str, min_grade: float, max_grade: float, 
           step_size: float, description: str = None) -> int:
        """Fügt ein neues Notensystem hinzu.
        
        Args:
            name: Name des Notensystems
            min_grade: Minimale Note
            max_grade: Maximale Note
            step_size: Schrittweite (z.B. 0.33 für 1-6 mit + und -)
            description: Optional, Beschreibung
            
        Returns:
            ID des neu erstellten Notensystems
        """
        cursor = self.execute(
            """INSERT INTO grading_systems 
               (name, min_grade, max_grade, step_size, description)
               VALUES (?, ?, ?, ?, ?)""",
            (name, min_grade, max_grade, step_size, description)
        )
        return cursor.lastrowid
    
    def get_by_id(self, system_id: int) -> Optional[Dict[str, Any]]:
        """Holt ein einzelnes Notensystem.
        
        Args:
            system_id: ID des Notensystems
            
        Returns:
            Dictionary mit Notensystemdaten oder None
        """
        cursor = self.execute(
            "SELECT * FROM grading_systems WHERE id = ?",
            (system_id,)
        )
        row = cursor.fetchone()
        return self._dict_from_row(row)
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Holt alle verfügbaren Notensysteme.
        
        Returns:
            Liste von Dictionaries mit Notensystemdaten, sortiert nach Name
        """
        cursor = self.execute(
            "SELECT * FROM grading_systems ORDER BY name"
        )
        return self._dicts_from_rows(cursor.fetchall())
    
    def update(self, system_id: int, name: str, min_grade: float,
               max_grade: float, step_size: float, description: str = None) -> None:
        """Aktualisiert ein bestehendes Notensystem.
        
        Args:
            system_id: ID des Notensystems
            name: Neuer Name
            min_grade: Neue minimale Note
            max_grade: Neue maximale Note
            step_size: Neue Schrittweite
            description: Optional, neue Beschreibung
        """
        self.execute(
            """UPDATE grading_systems 
               SET name = ?, min_grade = ?, max_grade = ?, 
                   step_size = ?, description = ?
               WHERE id = ?""",
            (name, min_grade, max_grade, step_size, description, system_id)
        )
    
    def delete(self, system_id: int) -> None:
        """Löscht ein Notensystem.
        
        Args:
            system_id: ID des zu löschenden Notensystems
        """
        self.execute(
            "DELETE FROM grading_systems WHERE id = ?",
            (system_id,)
        )
    
    def validate_grade(self, grade: float, system_id: int) -> bool:
        """Prüft ob eine Note in einem Notensystem gültig ist.
        
        Args:
            grade: Die zu prüfende Note
            system_id: ID des Notensystems
            
        Returns:
            True wenn die Note gültig ist, sonst False
        """
        system = self.get_by_id(system_id)
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
    
    def get_by_course(self, course_id: int) -> Optional[Dict[str, Any]]:
        """Holt das Notensystem für einen Kurs über dessen Template.
        
        Versucht zuerst über die template_id des Kurses, falls vorhanden.
        Falls keine template_id vorhanden ist, wird None zurückgegeben.
        
        Args:
            course_id: ID des Kurses
            
        Returns:
            Dictionary mit Notensystemdaten oder None
        """
        # Versuche zuerst über die template_id des Kurses
        cursor = self.execute(
            """SELECT gs.* 
            FROM courses c
            JOIN assessment_type_templates att ON c.template_id = att.id
            JOIN grading_systems gs ON att.grading_system_id = gs.id
            WHERE c.id = ? AND c.template_id IS NOT NULL""",
            (course_id,)
        )
        row = cursor.fetchone()
        if row:
            return self._dict_from_row(row)
        
        # Falls keine template_id vorhanden ist, gibt es kein Notensystem
        # (assessment_types haben keine direkte Verbindung zu grading_systems)
        return None
