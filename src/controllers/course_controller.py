# src/controllers/course_controller.py

"""
Controller für Kurs-Operationen.

Kapselt Business-Logik und Datenaggregation für Kurs-bezogene Operationen.
"""

from typing import Dict, List, Any, Optional
from .base_controller import BaseController


class CourseController(BaseController):
    """Controller für Kurs-Operationen."""
    
    def get_course(self, course_id: int) -> Optional[Dict[str, Any]]:
        """Holt einen Kurs anhand seiner ID.
        
        Args:
            course_id: ID des Kurses
            
        Returns:
            Dictionary mit Kursdaten oder None
        """
        return self.course_repo.get_by_id(course_id)
    
    def get_all_courses(self) -> List[Dict[str, Any]]:
        """Holt alle Kurse aus der Datenbank.
        
        Returns:
            Liste von Dictionaries mit Kursdaten, sortiert nach Name
        """
        return self.course_repo.get_all()
    
    def create_course(self, name: str, type: str = "course", subject: Optional[str] = None,
                     description: Optional[str] = None, color: Optional[str] = None,
                     template_id: Optional[int] = None) -> int:
        """Erstellt einen neuen Kurs.
        
        Args:
            name: Name des Kurses
            type: Typ ('class' oder 'course')
            subject: Optional, Fach
            description: Optional, Beschreibung
            color: Optional, Farbe (Hex-Code)
            template_id: Optional, ID der Bewertungstyp-Vorlage
            
        Returns:
            ID des neu erstellten Kurses
        """
        course_id = self.course_repo.add(name, type, subject, description, color, template_id)
        
        # Wenn Template ausgewählt wurde, Bewertungstypen erstellen
        if template_id:
            self.assessment_type_repo.create_from_template(course_id, template_id)
        
        return course_id
    
    def update_course(self, course_id: int, name: str, type: str = None,
                     subject: Optional[str] = None, description: Optional[str] = None,
                     color: Optional[str] = None, template_id: Optional[int] = None) -> None:
        """Aktualisiert die Daten eines Kurses.
        
        Args:
            course_id: ID des Kurses
            name: Neuer Name
            type: Optional, neuer Typ
            subject: Optional, neues Fach
            description: Optional, neue Beschreibung
            color: Optional, neue Farbe
            template_id: Optional, neue Template-ID
        """
        self.course_repo.update(course_id, name, type, subject, description, color, template_id)
    
    def delete_course(self, course_id: int) -> None:
        """Löscht einen Kurs.
        
        Args:
            course_id: ID des zu löschenden Kurses
        """
        self.course_repo.delete(course_id)
    
    def get_course_lessons(self, course_id: int) -> List[Dict[str, Any]]:
        """Holt alle Stunden eines Kurses.
        
        Args:
            course_id: ID des Kurses
            
        Returns:
            Liste von Dictionaries mit Stundendaten inkl. Kompetenzen
        """
        cursor = self.db.execute("""
            SELECT DISTINCT 
                l.id,
                l.date,
                l.time,
                l.topic,
                l.duration,
                l.status,
                l.status_note,
                GROUP_CONCAT(c.area || ': ' || c.description) as competencies
            FROM lessons l
            LEFT JOIN lesson_competencies lc ON l.id = lc.lesson_id
            LEFT JOIN competencies c ON lc.competency_id = c.id
            WHERE l.course_id = ?
            GROUP BY l.id
            ORDER BY l.date DESC, l.time DESC
        """, (course_id,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows] if rows else []
    
    def get_course_grades(self, course_id: int) -> List[Dict[str, Any]]:
        """Holt alle Noten eines Kurses.
        
        Args:
            course_id: ID des Kurses
            
        Returns:
            Liste von Dictionaries mit Notendaten
        """
        cursor = self.db.execute("""
            SELECT 
                a.id,
                l.date,
                s.first_name || ' ' || s.last_name as student_name,
                s.id as student_id,
                GROUP_CONCAT(c.area || ': ' || a.grade) as competencies,
                at.name as assessment_type,
                AVG(a.grade) as average
            FROM assessments a
            JOIN lessons l ON a.lesson_id = l.id
            JOIN students s ON a.student_id = s.id
            LEFT JOIN lesson_competencies lc ON l.id = lc.lesson_id
            LEFT JOIN competencies c ON lc.competency_id = c.id
            LEFT JOIN assessment_types at ON a.assessment_type_id = at.id
            WHERE l.course_id = ?
            GROUP BY a.id, l.date, s.id, at.id
            ORDER BY l.date DESC, s.last_name, s.first_name
        """, (course_id,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows] if rows else []
    
    def get_course_grades_detailed(self, course_id: int) -> List[Dict[str, Any]]:
        """Holt alle Bewertungen eines Kurses mit detaillierten Informationen.
        
        Diese Methode liefert gruppierte Bewertungen mit Durchschnitten und
        Kompetenz-Informationen für die Anzeige im Kurs-Tab.
        
        Args:
            course_id: ID des Kurses
            
        Returns:
            Liste von Dictionaries mit Bewertungsdaten:
            - date: Datum der Bewertung
            - student_name: Name des Schülers
            - competencies: Kompetenzen (GROUP_CONCAT)
            - assessment_type: Art der Bewertung
            - average_grade: Durchschnittsnote
            - topic: Thema der Bewertung
            - student_count: Anzahl der Schüler
            - lesson_id: ID der Stunde
        """
        cursor = self.db.execute("""
            SELECT 
                a.date,
                s.first_name || ' ' || s.last_name as student_name,
                GROUP_CONCAT(c.area || ': ' || c.description) as competencies,
                at.name as assessment_type,
                ROUND(AVG(a.grade), 2) as average_grade,
                a.topic,
                COUNT(DISTINCT s.id) as student_count,
                a.lesson_id
            FROM assessments a
            JOIN students s ON a.student_id = s.id
            JOIN assessment_types at ON a.assessment_type_id = at.id
            LEFT JOIN lessons l ON a.lesson_id = l.id
            LEFT JOIN lesson_competencies lc ON l.id = lc.lesson_id
            LEFT JOIN competencies c ON lc.competency_id = c.id
            WHERE a.course_id = ?
            GROUP BY a.date, a.topic, at.id
            ORDER BY a.date DESC, at.name
        """, (course_id,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows] if rows else []
    
    def get_courses_by_semester(self, semester_id: int) -> List[Dict[str, Any]]:
        """Holt alle Kurse eines Semesters.
        
        Args:
            semester_id: ID des Semesters
            
        Returns:
            Liste von Dictionaries mit Kursdaten
        """
        return self.course_repo.get_by_semester(semester_id)

    def get_courses_for_semester_dates(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Holt alle Kurse, die in einem bestimmten Semester aktiv sind.
        
        Args:
            start_date: Startdatum des Semesters (YYYY-MM-DD)
            end_date: Enddatum des Semesters (YYYY-MM-DD)
            
        Returns:
            Liste von Dictionaries mit Kurs-ID und Kurs-Name
        """
        cursor = self.course_repo.execute(
            """SELECT DISTINCT c.id, c.name 
            FROM courses c
            JOIN student_courses sc ON c.id = sc.course_id
            JOIN semester_history sh ON sc.semester_id = sh.id
            WHERE sh.start_date = ? AND sh.end_date = ?
            ORDER BY c.name""",
            (start_date, end_date)
        )
        return self.course_repo._dicts_from_rows(cursor.fetchall())
    
    def get_students_by_course(self, course_id: int, semester_id: int) -> List[Dict[str, Any]]:
        """Holt alle Schüler eines Kurses für ein bestimmtes Semester.
        
        Args:
            course_id: ID des Kurses
            semester_id: ID des Semesters
            
        Returns:
            Liste von Dictionaries mit Schülerdaten
        """
        cursor = self.db.execute("""
            SELECT s.* 
            FROM students s
            JOIN student_courses sc ON s.id = sc.student_id
            WHERE sc.course_id = ? AND sc.semester_id = ?
            ORDER BY s.last_name, s.first_name
        """, (course_id, semester_id))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows] if rows else []
