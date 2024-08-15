import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from student import Base, Student  # Make sure to import your Student model


def export_students_to_csv(output_file="students_export.csv"):
    # Create a database session
    engine = create_engine("postgresql://dev:111111@localhost/cms")
    Session = sessionmaker(bind=engine)
    session = Session()

    # Query all students
    students = session.query(Student).all()

    # Define the CSV headers based on your schema
    headers = [
        "Institution Name",
        "Academic Year",
        "Student Number",
        "FirstName",
        "Surname",
        "Date Of Birth",
        "Gender",
        "Nationality (Country)",
        "Number of Sponsors",
        "Type of Main Sponsor",
        "Name of Main Sponsor",
        "Faculty or School",
        "Programme",
        "Duration on programme",
        "Year of Study",
        "Qualification",
        "Level of Study",
        "Residential Status",
        "Student Status",
        "Mode of Study",
        "Disability Type",
        "Overall Exam Mark (%)",
        "Graduate Status",
        "Fees Application",
        "Fees Registration",
        "Fees Tuition",
        "Fee (Books)",
        "Fee (Accomodation Recommended)",
        "Fee (Accomodation Actual)",
        "Fee (Meals Recommended)",
        "Fee (Meals Actual)",
        "Fee (Lump Sum Recommended)",
        "Fee (Lump Sum Actual)",
        "OtherFees1Description",
        "Other Fees1 Value",
        "OtherFees2Description",
        "Other Fees 2 Value",
    ]

    # Write to CSV
    with open(output_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)

        for student in students:
            writer.writerow(
                [
                    student.institution_name,
                    student.academic_year,
                    student.student_number,
                    student.first_name,
                    student.surname,
                    student.date_of_birth,
                    student.gender,
                    student.nationality,
                    student.number_of_sponsors,
                    student.type_of_main_sponsor,
                    student.name_of_main_sponsor,
                    student.faculty_or_school,
                    student.program,
                    student.duration_on_program,
                    student.year_of_study,
                    student.qualification,
                    student.level_of_study,
                    student.residential_status,
                    student.student_status,
                    student.mode_of_study,
                    student.disability,
                    student.overall_exam_mark,
                    student.graduate_status,
                    student.fees_application,
                    student.fees_registration,
                    student.fees_tuition,
                    student.fee_books,
                    student.fee_accommodation_recommended,
                    student.fee_accommodation_actual,
                    student.fee_meals,
                    student.fee_meals_actual,
                    student.fee_lumpsum,
                    student.fee_lumpsum_actual,
                    student.other_fees1_description,
                    student.other_fees1_value,
                    student.other_fees2_description,
                    student.other_fees2_value,
                ]
            )

    print(f"Data exported to {output_file}")
    session.close()


if __name__ == "__main__":
    export_students_to_csv()
