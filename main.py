import logging
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from sqlalchemy import Column, Date, Float, Integer, String, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from browser import BASE_URL, Browser
from student import Session, Student

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class WebScraper:
    def __init__(self):
        self.browser = Browser()

    def scrape_student_list(self, url):
        try:
            response = self.browser.fetch(url)
            soup = BeautifulSoup(response.text, "lxml")
            students = []

            table = soup.find("table", id="ewlistmain")
            if not table:
                logger.warning(f"No student table found on page: {url}")
                return [], None

            rows = table.find_all("tr", class_=["ewTableRow", "ewTableAltRow"])

            for row in rows:
                columns = row.find_all("td")
                if len(columns) < 7:
                    logger.warning(f"Unexpected row format: {row}")
                    continue

                student = {
                    "school": columns[1].text.strip(),
                    "student_number": columns[3].text.strip(),
                    "name": columns[4].text.strip(),
                    "student_status": columns[6].text.strip(),
                }
                students.append(student)

            next_page = soup.find("a", text="Next")
            return students, next_page["href"] if next_page else None
        except Exception as e:
            logger.error(f"Error scraping student list: {str(e)}")
            return [], None

    def scrape_transcript(self, student_id):
        try:
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
        except Exception as e:
            logger.error(
                f"Error scraping transcript for student {student_id}: {str(e)}"
            )
            return None, None, None

    def scrape_details(self, student_id):
        try:
            url = f"{BASE_URL}/r_stdpersonalview.php?StudentID={student_id}"
            response = self.browser.fetch(url)
            soup = BeautifulSoup(response.text, "lxml")

            nationality = (
                soup.find("td", string="Nationality").find_next("td").text.strip()
            )
            sex = soup.find("td", string="Sex").find_next("td").text.strip()
            birthdate = soup.find("td", string="Birthdate").find_next("td").text.strip()
            birth_place = (
                soup.find("td", string="Birth Place").find_next("td").text.strip()
            )

            return nationality, sex, birthdate, birth_place
        except Exception as e:
            logger.error(f"Error scraping details for student {student_id}: {str(e)}")
            return None, None, None, None


def main():
    scraper = WebScraper()
    session = Session()

    student_list_url = f"{BASE_URL}/r_studentviewlist.php"

    try:
        while student_list_url:
            logger.info(f"Scraping student list from: {student_list_url}")
            students, next_page = scraper.scrape_student_list(student_list_url)

            new_students = []
            for student in students:
                logger.info(f"Processing student: {student['student_number']}")
                program, cgpa, academic_year = scraper.scrape_transcript(
                    student["student_number"]
                )
                nationality, sex, birthdate, birth_place = scraper.scrape_details(
                    student["student_number"]
                )

                if not all([program, cgpa, academic_year, nationality, sex, birthdate]):
                    logger.warning(
                        f"Incomplete data for student {student['student_number']}, skipping"
                    )
                    continue

                names = student["name"].split()
                first_name = names[0]
                surname = " ".join(names[1:])

                new_student = Student(
                    academic_year=academic_year,
                    student_number=int(student["student_number"]),
                    first_name=first_name,
                    surname=surname,
                    date_of_birth=birthdate,
                    gender=sex,
                    nationality=nationality,
                    faculty=student["school"],
                    program=program,
                    duration_of_program=3 if program.startswith("Diploma") else 4,
                    year_of_study=academic_year,
                    student_status=student["student_status"],
                    overall_exam_mark=int(
                        float(cgpa) * 20
                    ),  # Assuming CGPA is out of 5
                    graduate_status="Not Graduated",
                )
                new_students.append(new_student)

            try:
                session.bulk_save_objects(new_students)
                session.commit()
                logger.info(f"Saved {len(new_students)} students to the database")
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Error saving students to database: {str(e)}")

            if next_page:
                student_list_url = urljoin(BASE_URL, next_page)
            else:
                student_list_url = None
                logger.info("Finished scraping all student pages")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
