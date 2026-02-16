import os
import re


def transformedTextFiles2020(filename, semester, year):
    filePath = os.getcwd() + "/GradeDistributionsDB/" + semester + year
    os.chdir(filePath)

    with open(filename) as textFile:
        collect = False
        collect_init = False
        add_remainder = False
        add_end = False
        new_data = []
        lines = []
        on_index = 0

        for line in textFile:
            if line.strip() == 'COLLEGE:':
                collect = False
                collect_init = False
                add_remainder = False
                add_end = False
                new_data += lines
                lines = []
                on_index = 0

            if line.strip() == 'Cannot':
                break

            if line.strip() == '-------------------':
                collect = True
                collect_init = True

            if collect:
                remainder = re.compile(r"^ \d+").match(line.rstrip())
                found_ends_prof = re.compile(
                    r"\d+ \d\.\d+ \d+ \d+ \d+ \d+ \d+ \d+ (([a-zA-Z])+\s)+"
                ).match(line.strip())
                found_ends_totals = re.compile(
                    r"\d+ \d\.\d+ \d+ \d+ \d+ \d+ \d+ \d+"
                ).match(line.strip())

                if not add_end and (found_ends_prof is not None or found_ends_totals is not None):
                    add_remainder = False
                    add_end = True
                elif not add_remainder and not add_end and remainder is not None:
                    collect_init = False
                    add_remainder = True

                if collect_init:
                    match = re.compile(r"^\w+\-\d+\-\w+\s\d+").match(line)
                    if match is not None:
                        lines.append({"data": match.group(), "type": "section"})
                    else:
                        course_pattern = re.compile(r"^[A-Z]+ TOTAL: \d+")
                        course_match = course_pattern.match(line)
                        if course_match is not None:
                            lines.append({"data": course_match.group(), "type": "total"})
                elif add_remainder:
                    if on_index == len(lines):
                        on_index = 0
                    if len(lines) == 0:
                        continue
                    _lines = line.split("  ")
                    for item in _lines:
                        if '%' in item:
                            continue
                        _remainder = re.compile(r"^ \d+").match(item)
                        if _remainder is not None:
                            try:
                                lines[on_index]["data"] += _remainder.group().rstrip()
                            except Exception:
                                print("howdy")
                            on_index += 1
                elif add_end:
                    _lines = line.replace("Error", '0.000').strip().split("  ")
                    for part in _lines:
                        if on_index == len(lines):
                            on_index = 0

                        row_type = lines[on_index]["type"]
                        if row_type == "section":
                            matches = re.compile(
                                r"\d+ \d\.\d+ \d+ \d+ \d+ \d+ \d+ \d+ [\w+\s]*"
                            ).match(part.strip())
                            if matches is None:
                                part += " Not Listed"
                                matches = re.compile(
                                    r"\d+ \d\.\d+ \d+ \d+ \d+ \d+ \d+ \d+ [\w+\s]*"
                                ).match(part.strip())
                        elif row_type == "total":
                            matches = re.compile(
                                r"\d+ \d\.\d+ \d+ \d+ \d+ \d+ \d+ \d+"
                            ).match(part.strip())
                        else:
                            continue

                        if matches is not None:
                            lines[on_index]["data"] += (" " + matches.group())
                        else:
                            print("problem")
                        on_index += 1

        new_data += lines

    _transformed_list = []
    for row in new_data:
        if row["type"] == "section":
            professor = re.compile(r"[A-Z]+\s[A-Z]+$").search(row["data"])
            if professor is None:
                continue
            professor = professor.group()
            _transformed_list.append(row["data"].replace(professor, "").strip())
            _transformed_list.append(professor)

    from transformTextFiles import getCoursesWithProfessorsTransformed

    return getCoursesWithProfessorsTransformed(_transformed_list)
