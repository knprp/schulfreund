# src/controllers/student_controller.py

"""
Controller für Schüler-Operationen.

Kapselt Business-Logik und Datenaggregation für Schüler-bezogene Operationen.
"""

from typing import Dict, List, Any, Optional
from .base_controller import BaseController


class StudentController(BaseController):
    """Controller für Schüler-Operationen."""
    
    def get_student(self, student_id: int) -> Optional[Dict[str, Any]]:
        """Holt einen Schüler anhand seiner ID.
        
        Args:
            student_id: ID des Schülers
            
        Returns:
            Dictionary mit Schülerdaten oder None
        """
        return self.student_repo.get_by_id(student_id)
    
    def get_all_students(self) -> List[Dict[str, Any]]:
        """Holt alle Schüler aus der Datenbank.
        
        Returns:
            Liste von Dictionaries mit Schülerdaten, sortiert nach Nachname
        """
        return self.student_repo.get_all()
    
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
    
    def create_student(self, first_name: str, last_name: str) -> int:
        """Erstellt einen neuen Schüler.
        
        Args:
            first_name: Vorname des Schülers
            last_name: Nachname des Schülers
            
        Returns:
            ID des neu erstellten Schülers
        """
        return self.student_repo.add(first_name, last_name)
    
    def update_student(self, student_id: int, first_name: str, last_name: str) -> None:
        """Aktualisiert die Daten eines Schülers.
        
        Args:
            student_id: ID des Schülers
            first_name: Neuer Vorname
            last_name: Neuer Nachname
        """
        self.student_repo.update(student_id, first_name, last_name)
    
    def delete_student(self, student_id: int) -> None:
        """Löscht einen Schüler.
        
        Args:
            student_id: ID des zu löschenden Schülers
        """
        self.student_repo.delete(student_id)
    
    def add_student_to_course(self, student_id: int, course_id: int, semester_id: int) -> None:
        """Fügt einen Schüler zu einem Kurs hinzu.
        
        Args:
            student_id: ID des Schülers
            course_id: ID des Kurses
            semester_id: ID des Semesters
        """
        self.student_repo.add_to_course(student_id, course_id, semester_id)
    
    def get_student_course_grades(self, student_id: int) -> Dict[int, Dict[str, Any]]:
        """Holt die Gesamtnoten eines Schülers für alle seine Kurse.
        
        Args:
            student_id: ID des Schülers
            
        Returns:
            Dictionary mit Kurs-ID als Key und {'name': str, 'final_grade': float} als Value
        """
        return self.assessment_repo.get_student_course_grades(student_id)
    
    def get_student_competency_grades(self, student_id: int) -> Dict[str, Any]:
        """Berechnet die Durchschnittsnoten pro Kompetenzbereich für jeden Kurs eines Schülers.
        
        Args:
            student_id: ID des Schülers
            
        Returns:
            dict: {
                'areas': ['Bereich1', 'Bereich2', ...],  # Alle vorkommenden Kompetenzbereiche
                'grades': [  # Liste der Kurse mit ihren Kompetenznoten
                    {
                        'course_id': id,
                        'course_name': name,
                        'competencies': {
                            'Bereich1': note,
                            'Bereich2': note,
                            ...
                        }
                    },
                    ...
                ]
            }
        """
        try:
            # Erst alle vorkommenden Kompetenzbereiche ermitteln
            cursor = self.db.execute("""
                SELECT DISTINCT comp.area
                FROM assessments a
                JOIN lessons l ON a.lesson_id = l.id
                JOIN lesson_competencies lc ON l.id = lc.lesson_id
                JOIN competencies comp ON lc.competency_id = comp.id
                WHERE a.student_id = ?
                ORDER BY comp.area
            """, (student_id,))
            
            comp_areas = [row['area'] for row in cursor.fetchall()]
            
            # Dann die Noten pro Kurs und Kompetenzbereich holen
            cursor = self.db.execute("""
                SELECT 
                    c.id as course_id,
                    c.name as course_name,
                    comp.area as comp_area,
                    (SUM(a.grade * a.weight) / SUM(a.weight)) as avg_grade
                FROM assessments a
                JOIN courses c ON a.course_id = c.id
                JOIN lessons l ON a.lesson_id = l.id
                JOIN lesson_competencies lc ON l.id = lc.lesson_id
                JOIN competencies comp ON lc.competency_id = comp.id
                WHERE a.student_id = ?
                GROUP BY c.id, c.name, comp.area
                ORDER BY c.name, comp.area
            """, (student_id,))
            
            # Ergebnisse strukturieren
            grades_data = {}
            for row in cursor.fetchall():
                course_id = row['course_id']
                if course_id not in grades_data:
                    grades_data[course_id] = {
                        'course_id': course_id,
                        'course_name': row['course_name'],
                        'competencies': {}
                    }
                grades_data[course_id]['competencies'][row['comp_area']] = row['avg_grade']
            
            return {
                'areas': comp_areas,
                'grades': list(grades_data.values())
            }
            
        except Exception as e:
            print(f"DEBUG: Error in get_student_competency_grades: {str(e)}")
            raise
    
    def get_student_assessment_type_grades(self, student_id: int, course_id: int) -> List[Dict[str, Any]]:
        """Holt die Durchschnittsnoten pro Assessment Type für einen bestimmten Kurs.
        
        Args:
            student_id: ID des Schülers
            course_id: ID des Kurses
            
        Returns:
            Liste von Dictionaries mit Assessment Type Informationen und Noten
        """
        return self.assessment_repo.get_by_assessment_type(student_id, course_id)
    
    def get_student_courses(self, student_id: int) -> List[Dict[str, Any]]:
        """Holt alle Kurse eines Schülers.
        
        Args:
            student_id: ID des Schülers
            
        Returns:
            Liste von Dictionaries mit Kursdaten
        """
        cursor = self.db.execute("""
            SELECT c.*, sc.semester_id
            FROM courses c
            JOIN student_courses sc ON c.id = sc.course_id
            WHERE sc.student_id = ?
            ORDER BY c.name
        """, (student_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows] if rows else []
    
    def get_student_assessments(self, student_id: int) -> List[Dict[str, Any]]:
        """Holt alle Einzelnoten eines Schülers.
        
        Args:
            student_id: ID des Schülers
            
        Returns:
            Liste von Dictionaries mit Notendaten
        """
        cursor = self.db.execute("""
            SELECT 
                a.date,
                c.name as course_name,
                at.name as type_name,
                a.grade,
                COALESCE(a.topic, '') as topic,
                COALESCE(a.comment, '') as comment,
                a.lesson_id
            FROM assessments a
            JOIN courses c ON a.course_id = c.id
            JOIN assessment_types at ON a.assessment_type_id = at.id
            WHERE a.student_id = ?
            ORDER BY a.date DESC
        """, (student_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows] if rows else []
    
    def get_lesson_id_for_assessment(self, student_id: int, date: str) -> Optional[int]:
        """Holt die lesson_id für eine Bewertung anhand von Schüler-ID und Datum.
        
        Args:
            student_id: ID des Schülers
            date: Datum im Format 'YYYY-MM-DD'
            
        Returns:
            lesson_id oder None
        """
        cursor = self.db.execute("""
            SELECT lesson_id 
            FROM assessments
            WHERE student_id = ? 
            AND date = ?
            LIMIT 1
        """, (student_id, date))
        row = cursor.fetchone()
        return row['lesson_id'] if row and row['lesson_id'] else None
    
    def get_students_with_courses(self, semester_start: str = None, semester_end: str = None) -> List[Dict[str, Any]]:
        """Holt alle Schüler mit ihren Kursen für ein bestimmtes Semester.
        
        Args:
            semester_start: Startdatum des Semesters (optional)
            semester_end: Enddatum des Semesters (optional)
            
        Returns:
            Liste von Dictionaries mit Schülerdaten und deren Kursen
        """
        if semester_start and semester_end:
            # Hole Semester-ID
            semester = self.semester_repo.get_by_date(semester_start)
            if not semester:
                return []
            
            # Hole alle Schüler mit Kursen für dieses Semester
            cursor = self.db.execute("""
                SELECT DISTINCT s.*
                FROM students s
                JOIN student_courses sc ON s.id = sc.student_id
                JOIN semester_history sh ON sc.semester_id = sh.id
                WHERE sh.start_date = ? AND sh.end_date = ?
                ORDER BY s.last_name, s.first_name
            """, (semester_start, semester_end))
            
            students = [dict(row) for row in cursor.fetchall()] if cursor else []
            
            # Für jeden Schüler die Kurse laden
            for student in students:
                student['courses'] = []
                cursor = self.db.execute("""
                    SELECT c.*
                    FROM courses c
                    JOIN student_courses sc ON c.id = sc.course_id
                    WHERE sc.student_id = ? AND sc.semester_id = ?
                    ORDER BY c.name
                """, (student['id'], semester['id']))
                student['courses'] = [dict(row) for row in cursor.fetchall()] if cursor else []
            
            return students
        else:
            # Alle Schüler mit allen Kursen
            students = self.student_repo.get_all()
            for student in students:
                student['courses'] = self.get_student_courses(student['id'])
            return students
