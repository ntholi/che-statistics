import logging
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from sqlalchemy import Column, Date, Float, Integer, String, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database setup
engine = create_engine("postgresql://dev:111111@localhost/cms")
Base = declarative_base()
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


@dataclass()
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    academic_year = Column(Integer)
    student_number = Column(Integer)
    first_name = Column(String)
    surname = Column(String)
    date_of_birth = Column(String)
    gender = Column(String)
    nationality = Column(String)
    number_of_sponsors = Column(Integer, default=1)
    type_of_main_sponsor = Column(String, default="NMDS")
    name_of_main_sponsor = Column(String, default="NMDS")
    faculty = Column(String)
    program = Column(String)
    duration_of_program = Column(Integer)
    year_of_study = Column(Integer)
    qualification = Column(String, default="")
    level_of_study = Column(String, default="")
    residential_status = Column(String, default="Off-Campus")
    student_status = Column(String)
    mode_of_study = Column(String, default="Fulltime")
    disability = Column(String, default="N/A")
    overall_exam_mark = Column(Integer)
    graduate_status = Column(String)
    fees_applicable = Column(Integer, default=2)
    fees_registration = Column(Integer, default=1)
    fees_tuition = Column(Float)
    fee_books = Column(Integer, default=1)
    fee_accommodation = Column(Float)
    fee_accommodation_actual = Column(Float)
    fee_meals = Column(Float)
    fee_meals_actual = Column(Float)
    fee_lumpsum = Column(Float)
    fee_lumpsum_actual = Column(Float)
