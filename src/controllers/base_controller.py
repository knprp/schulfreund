# src/controllers/base_controller.py

"""
Basis-Controller-Klasse.

Stellt gemeinsame Funktionalität für alle Controller bereit,
insbesondere Zugriff auf den DatabaseManager und dessen Repositories.
"""

from typing import Any, Optional
from abc import ABC


class BaseController(ABC):
    """Basis-Klasse für alle Controller.
    
    Stellt gemeinsame Funktionalität bereit und gibt Zugriff
    auf den DatabaseManager und dessen Repositories.
    """
    
    def __init__(self, db_manager):
        """Initialisiert den Controller mit einem DatabaseManager.
        
        Args:
            db_manager: Instanz von DatabaseManager für Datenbankzugriffe
        """
        self.db = db_manager
    
    @property
    def student_repo(self):
        """Zugriff auf das StudentRepository."""
        return self.db.students
    
    @property
    def course_repo(self):
        """Zugriff auf das CourseRepository."""
        return self.db.courses
    
    @property
    def lesson_repo(self):
        """Zugriff auf das LessonRepository."""
        return self.db.lessons
    
    @property
    def competency_repo(self):
        """Zugriff auf das CompetencyRepository."""
        return self.db.competencies
    
    @property
    def assessment_repo(self):
        """Zugriff auf das AssessmentRepository."""
        return self.db.assessments
    
    @property
    def assessment_type_repo(self):
        """Zugriff auf das AssessmentTypeRepository."""
        return self.db.assessment_types
    
    @property
    def assessment_template_repo(self):
        """Zugriff auf das AssessmentTemplateRepository."""
        return self.db.assessment_templates
    
    @property
    def grading_system_repo(self):
        """Zugriff auf das GradingSystemRepository."""
        return self.db.grading_systems
    
    @property
    def semester_repo(self):
        """Zugriff auf das SemesterRepository."""
        return self.db.semesters
    
    @property
    def holiday_repo(self):
        """Zugriff auf das HolidayRepository."""
        return self.db.holidays
    
    @property
    def attendance_repo(self):
        """Zugriff auf das AttendanceRepository."""
        return self.db.attendance
    
    @property
    def settings_repo(self):
        """Zugriff auf das SettingsRepository."""
        return self.db.settings
