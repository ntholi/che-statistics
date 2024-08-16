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
            program = program_td.find_next("td").text.strip() if program_td else None

            results_td = soup.find_all("td", string="Results:")
            cgpa = (
                results_td[-1].find_next("td").text.strip().split(":")[-1].strip()
                if results_td
                else None
            )

            semester_tds = soup.find_all("td", string="Semester:")
            academic_year = (
                int(semester_tds[-1].find_next("td").text.split(",")[1].split()[1])
                if semester_tds
                else None
            )

            logger.info(
                f"Scraped transcript for student {student_id}: Program={program}, CGPA={cgpa}, Academic Year={academic_year}"
            )
            return program, cgpa, academic_year
        except Exception as e:
            logger.error(
                f"Error scraping transcript for student {student_id}: {str(e)}"
            )
            return None, None, None

    def scrape_program_list(self, student_id):
        try:
            url = f"{BASE_URL}/r_stdprogramlist.php?showmaster=1&StudentID={student_id}"
            response = self.browser.fetch(url)
            soup = BeautifulSoup(response.text, "lxml")

            program_row = soup.find("tr", class_=["ewTableRow", "ewTableAltRow"])

            if program_row:
                cells = program_row.find_all("td")
                if len(cells) >= 3:
                    program = cells[0].text.strip()
                    academic_year = cells[1].text.strip()

                    academic_year = int(
                        academic_year.split("-")[0]
                    )  # Adjust base year as needed

                    logger.info(
                        f"Scraped program list for student {student_id}: Program={program}, Academic Year={academic_year}"
                    )
                    return (
                        program,
                        "-1",
                        academic_year,
                    )  # Return -1 for CGPA as specified
                else:
                    logger.warning(
                        f"Insufficient data in program row for student {student_id}"
                    )
            else:
                logger.warning(
                    f"Program information row not found for student {student_id}"
                )

            return None, None, None
        except Exception as e:
            logger.error(
                f"Error scraping program list for student {student_id}: {str(e)}"
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

            program_row = soup.find("tr", class_=["ewTableRow", "ewTableAltRow"])

            if program_row:
                cells = program_row.find_all("td")
                asst_provider = cells[5].text.strip() if len(cells) >= 6 else ""
            else:
                logger.warning(
                    f"Program information row not found for student {student_id}"
                )
                asst_provider = ""

            logger.info(
                f"Scraped sponsor for student {student_id}: Asst-Provider={asst_provider}"
            )
            return asst_provider
        except Exception as e:
            logger.error(f"Error scraping sponsor for student {student_id}: {str(e)}")
            return ""


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
    if "diploma" in program.lower() or "associate" in program.lower():
        return 3
    elif "certificate" in program.lower():
        return 1
    return 4


def get_qualification(program: str):
    if "diploma" in program.lower() or "associate" in program.lower():
        return 1
    elif "certificate" in program.lower():
        return 2
    return 3


def get_student_status(program: str, year_of_study: int):
    program_duration = get_duration_of_program(program)
    return "Completer" if year_of_study == program_duration else "Continuing Student"


def get_tuition_fee(qualification: int, year_of_study: int):
    fee_map = {
        (1, 1): 12000,
        (2, 1): 19475,
        (2, 2): 19988,
        (3, 1): 19988,
    }
    return fee_map.get((qualification, year_of_study), 25625)


def process_student(scraper, student, session):
    try:
        student_number = student["student_number"]
        exists = session.query(Student).get(student_number)
        if exists:
            logger.warning(
                f"Student {student_number} already exists in the database, skipping"
            )
            return False

        program, cgpa, academic_year = scraper.scrape_transcript(student_number)

        if not all([program, cgpa, academic_year]):
            logger.info(
                f"Transcript data not found for student {student_number}, using fallback method"
            )
            program, cgpa, academic_year = scraper.scrape_program_list(student_number)

        nationality, sex, birthdate, birth_place = scraper.scrape_details(
            student_number
        )
        asst_provider = scraper.scrape_sponsor(student_number)

        if not all([program, cgpa, academic_year, sex, birthdate]):
            logger.warning(f"Incomplete data for student {student_number}, skipping")
            return False

        names = student["name"].split()
        surname = names[-1]
        first_name = " ".join(names[:-1])

        try:
            cgpa_float = float(cgpa)
            overall_exam_mark = int(cgpa_float * 25)
        except ValueError:
            logger.warning(f"Invalid CGPA value for student {student_number}: {cgpa}")
            overall_exam_mark = None

        qualification = get_qualification(program)
        new_student = Student(
            student_number=int(student_number),
            academic_year="2023/2024",
            first_name=first_name,
            surname=surname,
            date_of_birth=birthdate,
            gender=sex,
            nationality=nationality or "Unknown",
            faculty_or_school=get_faculty_or_school(student["school"]),
            program=program,
            duration_on_program=get_duration_of_program(program),
            year_of_study=academic_year,
            qualification=qualification,
            student_status=get_student_status(program, academic_year),
            overall_exam_mark=overall_exam_mark,
            graduate_status=(
                "Passed" if overall_exam_mark and overall_exam_mark >= 50 else "Failed"
            ),
            fees_tuition=get_tuition_fee(qualification, academic_year),
            type_of_main_sponsor="Government" if asst_provider == "NMDS" else "Other",
            name_of_main_sponsor=asst_provider or "Unknown",
        )

        session.add(new_student)
        session.commit()
        logger.info(f"Saved student {student_number} to the database")
        return True
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error saving student {student_number} to database: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error processing student {student_number}: {str(e)}")
        return False


def main():
    scraper = WebScraper()
    scraper.browser.login()
    session = Session()

    scraper.browser.fetch(
        "https://cmslesothosandbox.limkokwing.net/campus/registry/r_studentviewlist.php?x_InstitutionID=1&z_InstitutionID=%3D%2C%2C&x_LatestTerm=2022-08&z_LatestTerm=LIKE%2C%27%25%2C%25%27"
    )

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
                if process_student(scraper, student, session):
                    total_students_saved += 1
                total_students_processed += 1

                if total_students_processed % 10 == 0:
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
