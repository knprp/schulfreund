# src/controllers/__init__.py

"""
Controller-Layer für Schulfreund.

Controller kapseln Business-Logik und Datenaggregation und stellen
eine saubere Schnittstelle zwischen Views und Repositories dar.
"""

from .base_controller import BaseController
from .student_controller import StudentController
from .course_controller import CourseController
from .lesson_controller import LessonController
from .assessment_controller import AssessmentController
from .settings_controller import SettingsController
from .semester_controller import SemesterController
from .subject_controller import SubjectController
from .competency_controller import CompetencyController
from .grading_system_controller import GradingSystemController
from .assessment_template_controller import AssessmentTemplateController

__all__ = [
    'BaseController',
    'StudentController',
    'CourseController',
    'LessonController',
    'AssessmentController',
    'SettingsController',
    'SemesterController',
    'SubjectController',
    'CompetencyController',
    'GradingSystemController',
    'AssessmentTemplateController',
]
