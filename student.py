from sqlalchemy import Column, Float, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Student(Base):
    __tablename__ = "students"

    institution_name = Column(
        String, default="Limkokwing University of Creative Technology"
    )
    academic_year = Column(String)
    student_number = Column(Integer, primary_key=True)
    first_name = Column(String)
    surname = Column(String)
    date_of_birth = Column(String)
    gender = Column(String)
    nationality = Column(String)
    number_of_sponsors = Column(Integer, default=1)
    type_of_main_sponsor = Column(String)
    name_of_main_sponsor = Column(String)
    faculty_or_school = Column(String)
    program = Column(String)
    duration_on_program = Column(Integer)
    year_of_study = Column(Integer)
    qualification = Column(Integer)
    level_of_study = Column(String, default="UnderGraduate")
    residential_status = Column(String, default="Off-Campus")
    student_status = Column(String)
    mode_of_study = Column(String, default="Fulltime")
    disability = Column(String, default="N/A")
    overall_exam_mark = Column(Integer)
    graduate_status = Column(String)
    fees_application = Column(Integer, default=200)
    fees_registration = Column(Integer, default=1)
    fees_tuition = Column(Float)
    fee_books = Column(Integer, default=1)
    fee_accommodation_recommended = Column(Float, default=600.00)
    fee_accommodation_actual = Column(Float, default=600.00)
    fee_meals = Column(Float, default=1300.00)
    fee_meals_actual = Column(Float, default=1300.00)
    fee_lumpsum = Column(Float, default=7400.00)
    fee_lumpsum_actual = Column(Float, default=7400.00)
    other_fees1_description = Column(String, default="Laptop allowance")
    other_fees1_value = Column(Float, default=5000.00)
    other_fees2_description = Column(String, default="Data allowance")
    other_fees2_value = Column(Float, default=50.00)


engine = create_engine("postgresql://dev:111111@localhost/cms")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
