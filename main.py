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

    def scrape_sponsor(self, student_id):
        try:
            url = f"{BASE_URL}/r_stdprogramlist.php?showmaster=1&StudentID={student_id}"
            response = self.browser.fetch(url)
            soup = BeautifulSoup(response.text, "lxml")

            # Find the table row containing the program information
            program_row = soup.find("tr", class_=["ewTableRow", "ewTableAltRow"])

            if program_row:
                # The Asst-Provider is the 6th td element in the row
                cells = program_row.find_all("td")
                if len(cells) >= 6:
                    asst_provider = cells[5].text.strip()
                else:
                    logger.warning(
                        f"Asst-Provider information not found in the expected location for student {student_id}"
                    )
                    asst_provider = ""  # Default value
            else:
                logger.warning(
                    f"Program information row not found for student {student_id}"
                )
                asst_provider = ""  # Default value

            logger.info(
                f"Scraped sponsor for student {student_id}: Asst-Provider={asst_provider}"
            )
            return asst_provider
        except Exception as e:
            logger.error(f"Error scraping sponsor for student {student_id}: {str(e)}")
            return ""  # Default value in case of error


def get_faculty_or_school(code):
    faculty_map = {
        "FAID": "Faculty of Architecture and the Built Environment",
        "FBS": "Faculty of Business and Globalization",
        "FCM": "Faculty of Communication, Media and Broadcasting",
        "FCO": "Faculty of Communication, Media and Broadcasting",
        "FCTH": "Faculty of Creativity in Tourism & Hospitality",
        "FDSI": "Faculty of Design and Innovation",
        "FFLD": "Faculty of Design and Innovation",
        "FFTB": "Faculty of Communication, Media and Broadcasting",
        "FINT": "Faculty of Information & Communication Technology",
        "FMS": "Faculty of Communication, Media and Broadcasting",
    }
    return faculty_map.get(code, "Unknown")


def get_duration_of_program(program: str):
    if program.startswith("Diploma"):
        return 3
    elif program.startswith("Certificate"):
        return 1
    return 4


def get_qualification(program: str):
    if program.startswith("Certificate"):
        return 1
    elif program.startswith("Diploma"):
        return 2
    return 3


def get_student_status(program: str, year_of_study: int):
    program_duration = get_duration_of_program(program)
    if year_of_study == program_duration:
        return "Completer"
    return "Continuing Student"


def get_tuition_fee(qualification: int, year_of_study: int):
    if qualification == 1 and year_of_study == 1:
        return 12000
    elif qualification == 2 and year_of_study == 1:
        return 19475
    elif qualification == 2 and year_of_study >= 2:
        return 19988
    elif qualification == 3 and year_of_study == 1:
        return 19988
    elif qualification == 3 and year_of_study >= 2:
        return 25625


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
                asst_provider = scraper.scrape_sponsor(student["student_number"])

                if not all(
                    [
                        program,
                        cgpa,
                        academic_year,
                        nationality,
                        sex,
                        birthdate,
                        asst_provider,
                    ]
                ):
                    logger.warning(
                        f"Incomplete data for student {student['student_number']}, skipping"
                    )
                    continue

                names = student["name"].split()
                reversed_names = names[::-1]
                surname = reversed_names[0]
                first_name = " ".join(reversed_names[1:])

                try:
                    cgpa_float = float(cgpa)
                    overall_exam_mark = int(cgpa_float * 25)
                except ValueError:
                    logger.warning(
                        f"Invalid CGPA value for student {student['student_number']}: {cgpa}"
                    )
                    overall_exam_mark = None

                new_student = Student(
                    student_number=int(student["student_number"]),
                    academic_year="2023/2024",
                    first_name=first_name,
                    surname=surname,
                    date_of_birth=birthdate,
                    gender=sex,
                    nationality=nationality,
                    faculty_or_school=get_faculty_or_school(student["school"]),
                    program=program,
                    duration_on_program=get_duration_of_program(program),
                    year_of_study=academic_year,
                    qualification=get_qualification(program),
                    student_status=get_student_status(program, academic_year),
                    overall_exam_mark=overall_exam_mark,
                    graduate_status=(
                        "Passed"
                        if overall_exam_mark and overall_exam_mark >= 50
                        else "Failed"
                    ),
                    fees_tuition=get_tuition_fee(
                        get_qualification(program), academic_year
                    ),
                    type_of_main_sponsor=(
                        "Government" if asst_provider == "NMDS" else "Other"
                    ),
                    name_of_main_sponsor=asst_provider,
                )

                try:
                    exists = session.query(Student).get(new_student.student_number)
                    if exists:
                        logger.warning(
                            f"{total_students_saved}) Student {student['student_number']} already exists in the database, skipping"
                        )
                        continue
                    session.add(new_student)
                    session.commit()
                    total_students_saved += 1
                    logger.info(
                        f"{total_students_saved}) Saved student {student['student_number']} to the database"
                    )
                except SQLAlchemyError as e:
                    session.rollback()
                    logger.error(
                        f"{total_students_saved}) Error saving student {student['student_number']} to database: {str(e)}"
                    )

                total_students_processed += 1

                if total_students_processed % 10 == 0:  # Log progress every 10 students
                    logger.info(
                        f"Progress: Processed {total_students_processed} students, Saved {total_students_saved} students"
                    )

            if next_page:
                student_list_url = f"{BASE_URL}/{next_page}"
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
