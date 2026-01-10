# src/controllers/assessment_controller.py

"""
Controller für Bewertungs-/Noten-Operationen.

Kapselt Business-Logik und Datenaggregation für Noten-bezogene Operationen.
"""

from typing import Dict, List, Any, Optional
from .base_controller import BaseController


class AssessmentController(BaseController):
    """Controller für Bewertungs-/Noten-Operationen."""
    
    def add_or_update_assessment(self, data: Dict[str, Any] = None, 
                                student_id: int = None, lesson_id: int = None, 
                                grade: float = None, weight: float = 1.0, 
                                assessment_type_id: Optional[int] = None,
                                course_id: Optional[int] = None) -> int:
        """Fügt eine neue Bewertung hinzu oder aktualisiert eine bestehende.
        
        Args:
            data: Dictionary mit Bewertungsdaten (wenn angegeben, werden andere Parameter ignoriert)
            student_id: ID des Schülers (wenn data nicht angegeben)
            lesson_id: ID der Stunde (wenn data nicht angegeben)
            grade: Note (wenn data nicht angegeben)
            weight: Optional, Gewichtung (Standard: 1.0)
            assessment_type_id: Optional, ID des Bewertungstyps
            course_id: Optional, ID des Kurses (wird automatisch ermittelt, falls nicht angegeben)
            
        Returns:
            ID der Bewertung
        """
        if data:
            return self.assessment_repo.add_or_update(data)
        else:
            # Erstelle Dictionary aus Parametern
            assessment_data = {
                'student_id': student_id,
                'lesson_id': lesson_id,
                'grade': grade,
                'weight': weight,
                'assessment_type_id': assessment_type_id,
                'course_id': course_id
            }
            return self.assessment_repo.add_or_update(assessment_data)
    
    def delete_assessment(self, student_id: int, lesson_id: int) -> None:
        """Löscht eine Bewertung.
        
        Args:
            student_id: ID des Schülers
            lesson_id: ID der Stunde
        """
        self.assessment_repo.delete(student_id, lesson_id)
    
    def get_assessment(self, student_id: int, lesson_id: int) -> Optional[Dict[str, Any]]:
        """Holt eine Bewertung.
        
        Args:
            student_id: ID des Schülers
            lesson_id: ID der Stunde
            
        Returns:
            Dictionary mit Bewertungsdaten oder None
        """
        return self.assessment_repo.get_by_lesson(student_id, lesson_id)
    
    def get_assessments_by_course(self, course_id: int) -> List[Dict[str, Any]]:
        """Holt alle Bewertungen eines Kurses.
        
        Args:
            course_id: ID des Kurses
            
        Returns:
            Liste von Dictionaries mit Bewertungsdaten
        """
        return self.assessment_repo.get_by_course(course_id)
    
    def calculate_final_grade(self, student_id: int, course_id: int) -> Optional[float]:
        """Berechnet die Gesamtnote eines Schülers für einen Kurs.
        
        Args:
            student_id: ID des Schülers
            course_id: ID des Kurses
            
        Returns:
            Gesamtnote oder None, falls keine Noten vorhanden
        """
        return self.assessment_repo.calculate_final_grade(student_id, course_id)
    
    def get_student_course_grades(self, student_id: int) -> Dict[int, Dict[str, Any]]:
        """Holt die Gesamtnoten eines Schülers für alle seine Kurse.
        
        Args:
            student_id: ID des Schülers
            
        Returns:
            Dictionary mit Kurs-ID als Key und {'name': str, 'final_grade': float} als Value
        """
        return self.assessment_repo.get_student_course_grades(student_id)
    
    def get_statistics(self, course_id: int) -> Dict[str, Any]:
        """Holt Statistiken für einen Kurs.
        
        Args:
            course_id: ID des Kurses
            
        Returns:
            Dictionary mit Statistiken (Durchschnitt, Min, Max, etc.)
        """
        return self.assessment_repo.get_statistics(course_id)
    
    def get_absent_students(self, lesson_id: int) -> List[int]:
        """Holt die IDs aller abwesenden Schüler für eine Stunde.
        
        Args:
            lesson_id: ID der Stunde
            
        Returns:
            Liste von Schüler-IDs
        """
        return self.attendance_repo.get_absent_students(lesson_id)
    
    def mark_absent(self, lesson_id: int, student_id: int) -> None:
        """Markiert einen Schüler als abwesend.
        
        Args:
            lesson_id: ID der Stunde
            student_id: ID des Schülers
        """
        self.attendance_repo.mark_absent(lesson_id, student_id)
    
    def mark_present(self, lesson_id: int, student_id: int) -> None:
        """Markiert einen Schüler als anwesend.
        
        Args:
            lesson_id: ID der Stunde
            student_id: ID des Schülers
        """
        self.attendance_repo.mark_present(lesson_id, student_id)
    
    def get_first_assessment_for_lesson(self, lesson_id: int) -> Optional[Dict[str, Any]]:
        """Holt das erste Assessment einer Stunde (für Assessment-Typ-Info).
        
        Args:
            lesson_id: ID der Stunde
            
        Returns:
            Dictionary mit assessment_type_id und topic oder None
        """
        cursor = self.db.execute(
            """SELECT DISTINCT assessment_type_id, topic 
            FROM assessments 
            WHERE lesson_id = ? 
            LIMIT 1""",
            (lesson_id,)
        )
        row = cursor.fetchone()
        return self.assessment_repo._dict_from_row(row) if row else None
    
    def delete_assessments_by_lesson(self, lesson_id: int) -> int:
        """Löscht alle Assessments einer Stunde.
        
        Args:
            lesson_id: ID der Stunde
            
        Returns:
            Anzahl der gelöschten Assessments
        """
        cursor = self.db.execute(
            "DELETE FROM assessments WHERE lesson_id = ?",
            (lesson_id,)
        )
        return cursor.rowcount
    
    def get_assessment_types_for_course(self, course_id: int) -> List[Dict[str, Any]]:
        """Holt alle Bewertungstypen eines Kurses.
        
        Args:
            course_id: ID des Kurses
            
        Returns:
            Liste von Dictionaries mit Bewertungstypdaten
        """
        return self.assessment_type_repo.get_by_course(course_id)
    
    def delete_assessment_type(self, type_id: int) -> None:
        """Löscht einen Bewertungstyp.
        
        Args:
            type_id: ID des zu löschenden Bewertungstyps
        """
        self.assessment_type_repo.delete(type_id)
    
    def create_assessment_types_from_template(self, course_id: int, template_id: int) -> None:
        """Erstellt Bewertungstypen für einen Kurs aus einer Vorlage.
        
        Args:
            course_id: ID des Kurses
            template_id: ID der Vorlage
        """
        self.assessment_type_repo.create_from_template(course_id, template_id)
    
    def add_assessment_type(self, course_id: int, name: str,
                           parent_type_id: Optional[int] = None,
                           weight: float = 1.0) -> int:
        """Fügt einen neuen Bewertungstyp hinzu.
        
        Args:
            course_id: ID des Kurses
            name: Name des Bewertungstyps
            parent_type_id: Optional, ID des übergeordneten Typs
            weight: Gewichtung (Standard: 1.0)
            
        Returns:
            ID des neu erstellten Bewertungstyps
        """
        return self.assessment_type_repo.add(course_id, name, parent_type_id, weight)
    
    def update_assessment_type(self, type_id: int, name: str,
                              parent_type_id: Optional[int] = None,
                              weight: float = 1.0) -> None:
        """Aktualisiert einen Bewertungstyp.
        
        Args:
            type_id: ID des Bewertungstyps
            name: Neuer Name
            parent_type_id: Optional, neue Parent-ID
            weight: Neue Gewichtung
        """
        self.assessment_type_repo.update(type_id, name, parent_type_id, weight)
    
    def get_grading_system_for_course(self, course_id: int) -> Optional[Dict[str, Any]]:
        """Holt das Notensystem für einen Kurs.
        
        Args:
            course_id: ID des Kurses
            
        Returns:
            Dictionary mit Notensystemdaten oder None
        """
        return self.grading_system_repo.get_by_course(course_id)
