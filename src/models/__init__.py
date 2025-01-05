# src/models/__init__.py

from .course.course import Course
from .student.student import Student
from .student.remarks import StudentRemark

__all__ = [
    'Course',
    'Student',
    'StudentRemark'
]