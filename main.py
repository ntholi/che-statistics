import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from sqlalchemy.exc import SQLAlchemyError

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

            logger.info(f"Scraped {len(students)} students from the current page")

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

            program_td = soup.find("td", string="Program:")
            if program_td:
                program = program_td.find_next("td").text.strip()
            else:
                logger.warning(
                    f"Program information not found for student {student_id}"
                )
                program = None

            results_td = soup.find_all("td", string="Results:")
            if results_td:
                cgpa_text = results_td[-1].find_next("td").text.strip()
                cgpa = cgpa_text.split(":")[-1].strip()
            else:
                logger.warning(f"CGPA information not found for student {student_id}")
                cgpa = None

            semester_tds = soup.find_all("td", string="Semester:")
            if semester_tds:
                last_semester_td = semester_tds[-1]
                semester_text = last_semester_td.find_next("td").text
                academic_year = int(semester_text.split(",")[1].split()[1])
            else:
                logger.warning(
                    f"Academic year information not found for student {student_id}"
                )
                academic_year = None

            logger.info(
                f"Scraped transcript for student {student_id}: Program={program}, CGPA={cgpa}, Academic Year={academic_year}"
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

            logger.info(
                f"Scraped details for student {student_id}: Nationality={nationality}, Sex={sex}, Birthdate={birthdate}"
            )
            return nationality, sex, birthdate, birth_place
        except Exception as e:
            logger.error(f"Error scraping details for student {student_id}: {str(e)}")
            return None, None, None, None


def main():
    scraper = WebScraper()
    session = Session()

    student_list_url = f"{BASE_URL}/r_studentviewlist.php"
    page_number = 1
    total_students_processed = 0
    total_students_saved = 0

    try:
        while student_list_url:
            logger.info(
                f"Scraping student list from page {page_number}: {student_list_url}"
            )
            students, next_page = scraper.scrape_student_list(student_list_url)

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

                try:
                    cgpa_float = float(cgpa)
                    overall_exam_mark = int(cgpa_float * 20)
                except ValueError:
                    logger.warning(
                        f"Invalid CGPA value for student {student['student_number']}: {cgpa}"
                    )
                    overall_exam_mark = None

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
                    duration_of_program=(
                        3 if program and program.startswith("Diploma") else 4
                    ),
                    year_of_study=academic_year,
                    student_status=student["student_status"],
                    overall_exam_mark=overall_exam_mark,
                    graduate_status="Not Graduated",
                )

                try:
                    session.add(new_student)
                    session.commit()
                    total_students_saved += 1
                    logger.info(
                        f"Saved student {student['student_number']} to the database"
                    )
                except SQLAlchemyError as e:
                    session.rollback()
                    logger.error(
                        f"Error saving student {student['student_number']} to database: {str(e)}"
                    )

                total_students_processed += 1

                if total_students_processed % 10 == 0:  # Log progress every 10 students
                    logger.info(
                        f"Progress: Processed {total_students_processed} students, Saved {total_students_saved} students"
                    )

            if next_page:
                student_list_url = urljoin(BASE_URL, next_page)
                page_number += 1
            else:
                student_list_url = None
                logger.info(
                    f"Finished scraping all student pages. Total students processed: {total_students_processed}, Total students saved: {total_students_saved}"
                )

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
