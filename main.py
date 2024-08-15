import logging
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from sqlalchemy import Column, Date, Float, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from browser import BASE_URL, Browser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()


@dataclass()
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    academic_year = Column(Integer)
    student_number = Column(Integer)
    first_name = Column(String)
    surname = Column(String)
    date_of_birth = Column(Date)
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


# Database setup
engine = create_engine("postgresql://dev:111111@localhost/cms")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


class WebScraper:
    def __init__(self):
        self.browser = Browser()

    def scrape_student_list(self, url):
        response = self.browser.fetch(url)
        soup = BeautifulSoup(response.text, "lxml")
        students = []

        table = soup.find("table", id="ewlistmain")
        rows = table.find_all("tr", class_=["ewTableRow", "ewTableAltRow"])

        for row in rows:
            columns = row.find_all("td")
            school = columns[1].text.strip()
            student_number = columns[3].text.strip()
            name = columns[4].text.strip()
            student_status = columns[6].text.strip()

            student = {
                "school": school,
                "student_number": student_number,
                "name": name,
                "student_status": student_status,
            }
            students.append(student)

        next_page = soup.find("a", text="Next")
        return students, next_page["href"] if next_page else None

    def scrape_transcript(self, student_id):
        url = f"{BASE_URL}/Officialreport.php?showmaster=1&StudentID={student_id}"
        response = self.browser.fetch(url)
        soup = BeautifulSoup(response.text, "lxml")

        program = soup.find("td", string="Program:").find_next("td").text.strip()
        cgpa = (
            soup.find_all("td", string="Results:")[-1]
            .find_next("td")
            .text.split("/")[-1]
            .strip()
        )
        academic_year = int(
            soup.find("td", string="Semester:")
            .find_next("td")
            .text.split(",")[1]
            .split()[1]
        )

        return program, cgpa, academic_year

    def scrape_details(self, student_id):
        url = f"{BASE_URL}/r_stdpersonalview.php?StudentID={student_id}"
        response = self.browser.fetch(url)
        soup = BeautifulSoup(response.text, "lxml")

        nationality = soup.find("td", string="Nationality").find_next("td").text.strip()
        sex = soup.find("td", string="Sex").find_next("td").text.strip()
        birthdate = soup.find("td", string="Birthdate").find_next("td").text.strip()
        birth_place = soup.find("td", string="Birth Place").find_next("td").text.strip()

        return nationality, sex, birthdate, birth_place


def main():
    scraper = WebScraper()
    session = Session()

    student_list_url = f"{BASE_URL}/r_studentviewlist.php"

    while student_list_url:
        students, next_page = scraper.scrape_student_list(student_list_url)

        for student in students:
            program, cgpa, academic_year = scraper.scrape_transcript(
                student["student_number"]
            )
            nationality, sex, birthdate, birth_place = scraper.scrape_details(
                student["student_number"]
            )

            names = student["name"].split()
            first_name = names[0]
            surname = " ".join(names[1:])

            new_student = Student(
                academic_year=academic_year,
                student_number=int(student["student_number"]),
                first_name=first_name,
                surname=surname,
                date_of_birth=datetime.strptime(birthdate, "%Y-%m-%d").date(),
                gender=sex,
                nationality=nationality,
                faculty=student["school"],
                program=program,
                duration_of_program=3 if program.startswith("Diploma") else 4,
                year_of_study=academic_year,
                student_status=student["student_status"],
                overall_exam_mark=int(float(cgpa) * 20),  # Assuming CGPA is out of 5
                graduate_status="Not Graduated",
            )

            session.add(new_student)
            session.commit()

        if next_page:
            student_list_url = urljoin(BASE_URL, next_page)
        else:
            student_list_url = None

    session.close()


if __name__ == "__main__":
    main()
