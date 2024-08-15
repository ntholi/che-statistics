from dataclasses import dataclass


@dataclass()
class Student:
    academic_year: int
    student_number: int
    first_name: str
    surname: str
    date_of_birth: str
    gender: str
    nationality: str
    number_of_sponsors = 1
    type_of_main_sponsor: str
    name_of_main_sponsor: str
    faculty: str
    program: str
    duration_of_program: int
    year_of_study: int
    qualification: str
    level_of_study: str
    residential_status: str
    student_status: str
    mode_of_study = "Fulltime"
    disability = "N/A"
    overall_exam_mark: int
    graduate_status: str
    fees_applicable = 2
    fees_registration = 1
    fees_tuition: float
    fee_books = 1
    fee_accommodation: float
    fee_accommodation_actual: float
    fee_meals: float
    fee_meals_actual: float
    fee_lumpsum: float
    fee_lumpsum_actual: float
