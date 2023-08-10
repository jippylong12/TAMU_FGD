from pypdf import PdfReader
import re

from transformTextFiles import getCoursesWithProfessorsTransformed


class PdfAnalyzer:
    def __init__(self, pdf_file):
        self.pdf_file = pdf_file

    # from Spring 2012 - ??
    def transform_v1(self):
        reader = PdfReader(self.pdf_file)
        unsplit_master_list = []
        split_master_list = []
        text_list = []
        for page in reader.pages:
            print(f"Page: #{page.page_number + 1}")
            text_list += page.extract_text().split("\n")
        state = 'search'
        current_data = [
            # first part AGCJ-105-500
            # middle part '19.75%   16    47    12     4      2    81     0    0    0    0    0     81'
            # last part 2.876 DUNSFORD D
        ]
        for line in text_list:
            if state == 'collect':
                course_info = re.compile(r"\w+\-\d+\-\w+ \d\.\d+ ([a-zA-Z]*\s*)*").match(line)
                if course_info is not None:
                    state = 'found_data'
                    first_part = re.compile(r"\w+\-\d+\-\w+").match(line)
                    if first_part is None:
                        print(line)
                        raise("Should not happen - the first part should always have a course")

                    first_part = first_part.group()
                    current_data.append(first_part)

                    last_part_one = re.compile(r"\d\.\d+").findall(line)
                    if len(last_part_one) == 0:
                        print(line)
                        raise("Should not happen - the last_part should always exist with GPA and prof name")
                    current_data.append(last_part_one[0])

                    last_part_two = re.compile(r"[A-Z\- ]{2,}$").findall(line)
                    if len(last_part_two) == 0:
                        print(line)
                        raise("Should not happen - the last_part should always exist with GPA and prof name")
                    current_data.append(last_part_two[0].strip())

            elif state == 'found_data':
                middle_part = re.compile(r"\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+").findall(line)
                if len(middle_part) == 0:
                    print(line)
                    raise("Middle part should not be missing")

                middle_part_one = " ".join(middle_part[0].split()[0:6])
                middle_part_two = " ".join(middle_part[0].split()[6:])
                current_data.insert(1, middle_part_one)
                current_data.insert(3, middle_part_two)
                unsplit_master_list.append(" ".join(current_data))
                current_data = []
                state = 'collect'
            elif state == 'search' and 'GRADE DISTRIBUTION REPORT' in line:
                state = 'collect'


        for row in unsplit_master_list:
            # only operate on the sections for the professors
            # try to find the name
            professor = re.compile(r"[A-Z\- ]{2,}$").search(row)
            if professor is None:
                raise "Prof name not found"
            else:
                professor = professor.group()

            # we will feed into the master dictionary a list that will have all course data on row A and the professor name on row B
            split_master_list.append(row.replace(professor, "").strip())
            split_master_list.append(professor)
        return getCoursesWithProfessorsTransformed(split_master_list)



