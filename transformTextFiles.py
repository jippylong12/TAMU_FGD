from __future__ import print_function
import os
import re
from Queue import Queue
from collections import defaultdict


def getCoursesWithProfessorsTransformed(usefulData):
    # setting everything up
    masterDictionary = defaultdict(list)

    currentCourse = ""
    tempCourseInfo = ""

    # for each line use regex to find the course info and professor infor and
    # add them to the master dictionary
    for line in usefulData:
        course_fmt = r"\w+-\d+-\d+ \d+ \d+ \d+ \d+ \d+ \d+ \d.\d+ \d+ \d+ \d+ \d+ \d+ \d+"
        foundCourseMatch = re.search(course_fmt, line)
        # if we found the course line we add it
        if foundCourseMatch is not None:
            tempCourseInfo = foundCourseMatch.group()
            # get the course name
            currentCourse = tempCourseInfo[:8]
        # try to find a professor
        foundProfessor = re.match("[A-Z]+ [A-Z]", line)
        # if we found a professor
        if foundProfessor is not None:
            # add it to the master dictionary
            masterDictionary[currentCourse].append(
                (tempCourseInfo, foundProfessor.group()))

    return masterDictionary


# I fixed the issue that included the end cases. But then I ran into another issue where the new PDFs have errors in them and
# so you have to manually fix the errors. They literally say "Error" and they are typically occurring with 4.00.
# I just open all text files and search and replace. You also have to change the 0.000 to 4.000 which are typically a few lines above it.
def transformedTextFiles(filename, semester, year):
    filePath = os.getcwd() + "/GradeDistributionsDB/" + semester + year
    os.chdir(filePath)

    beginningQ = Queue()
    endQ = Queue()

    middleCount = 0
    extraCount = 0
    extraMiddleCount = 0

    middleString = ""
    extraMiddleString = ""

    transformedString = ""

    with open(filename) as textFile:
        heading_skip = False
        for line in textFile:
            if line.strip() == '________________':
                heading_skip = True
            elif line.strip() == '-------------------':
                middleCount = 0
                extraMiddleCount = 0
                endQ.queue.clear()
                heading_skip = False
            elif heading_skip:
                continue
            elif re.match(r"\w+-\d+-\w\d+\s\d+", line) is not None:  # COURSE LINES
                extraMiddleCount = 0
                data = re.match(r"\w+-\d+-\w\d+\s\d+", line).group(0)
                beginningQ.put(data)
            elif re.match(r"\w+\s\w+:\s\d+", line) is not None:  # COURSE TOTAL LINE
                extraMiddleCount = 0
                data = re.match(r"\w+\s\w+:\s\d+", line).group(0)
                beginningQ.put(data)
            elif re.match(r"\d+\s\d.\d+\s\d+\s\d+\s\d+\s\d+\s\d+\s\d+\s[A-Z-]+[ [A-Z]{3,}", line):  # MORE INFORMATION
                data = re.match(r"\d+\s\d.\d+\s\d+\s\d+\s\d+\s\d+\s\d+\s\d+\s[A-Z-]+[ [A-Z]{3,}", line)
                data = data.group(0).strip()
                endQ.put(data)

                if middleString != "":
                    transformedString = transformedString + beginningQ.get() + ' ' + middleString + endQ.get() + '\n\n'
                    middleCount = 0
                    middleString = ""

                if extraMiddleCount < 4:
                    extraMiddleCount = 0
                else:
                    transformedString = transformedString + beginningQ.get() + ' ' + extraMiddleString + data + '\n\n'
                    extraMiddleCount = 0
                    extraMiddleString = ""
                    middleCount = 4

            elif re.match(r"\d+\s\d.\d+\s\d+\s\d+\s\d+\s\d+\s\d+\s\d+", line):
                data = re.match(r"\d+\s\d.\d+\s\d+\s\d+\s\d+\s\d+\s\d+\s\d+", line)
                data = data.group(0)
                endQ.put(data)

                if middleString != "":
                    transformedString = transformedString + beginningQ.get() + ' ' + middleString + endQ.get() + '\n\n'
                    middleCount = 0
                    middleString = ""

                if extraMiddleCount < 4:
                    extraMiddleCount = 0
                else:
                    transformedString = transformedString + beginningQ.get() + ' ' + extraMiddleString + data + '\n\n'
                    extraMiddleCount = 0
                    extraMiddleString = ""
                    middleCount = 4

            else:  # GET ALL THE MIDDLE STUFF
                if middleCount < 4:
                    if re.match(r"\d+", line) is not None:  # I think it has to deal with the ----- cut of the pages
                        number = re.match(r"\d+", line)
                        number = number.group(0)
                        middleString = middleString + number + ' '
                        middleCount += 1
                else:
                    if extraMiddleCount < 3:
                        extraMiddleCount += 1
                    else:
                        if re.match(r"\d+", line) is not None:  # I think it has to deal with the ----- cut of the pages
                            number = re.match(r"\d+", line)
                            number = number.group(0)
                            extraMiddleString = extraMiddleString + number + ' '
                            extraMiddleCount += 1

    # ONCE HERE IT HAS TRANSFORMED THE FILE. NOW WE JUST NEED TO PUT THE PROFESSOR NAMES ON A NEW LINE AND THEN
    # JUST RUN THE OLD FUNCTIONS ON IT.

    transformedString = transformedString.split("\n")
    newTransformedString = ""
    for line in transformedString:
        try:
            lineOne = re.match(r"\w+-\d+-\d+\s\d+\s\d+\s\d+\s\d+\s\d+\s\d+\s\d+.\d+\s\d+\s\d+\s\d+\s\d+\s\d+\s\d+",
                               line)
            lineOne = lineOne.group(0)
            lineTwo = re.split(r"\w+-\d+-\d+\s\d+\s\d+\s\d+\s\d+\s\d+\s\d+\s\d+.\d+\s\d+\s\d+\s\d+\s\d+\s\d+\s\d+\s",
                               line)
            lineTwo = lineTwo[1]
            newTransformedString = newTransformedString + lineOne + '\n\n' + lineTwo + '\n\n'
        except:
            continue

    newTransformedString = newTransformedString.split('\n\n')

    # NOW NEW TRANSFORMED STRING IS IN THE CORRECT FORMAT
    return getCoursesWithProfessorsTransformed(newTransformedString)


def transformedTextFiles2020(filename,semester,year):

    filePath = os.getcwd() + "/GradeDistributionsDB/" + semester + year
    os.chdir(filePath)

    course_index_to_skip = []

    _list = []
    num_of_courses = 0

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

            if line.strip() == '-------------------':
                collect = True
                collect_init = True

            if collect:
                remainder = re.compile(r"^ \d+").match(line.rstrip())
                found_ends_prof = re.compile(r"\d+ \d\.\d+ \d+ \d+ \d+ \d+ \d+ \d+ (([a-zA-Z])+\s)+").match(line.strip())
                found_ends_totals = re.compile(r"\d+ \d\.\d+ \d+ \d+ \d+ \d+ \d+ \d+").match(line.strip())

                if not add_end and (found_ends_prof is not None or found_ends_totals is not None):
                    add_remainder = False
                    add_end = True
                elif not add_remainder and not add_end and remainder is not None:
                    collect_init = False
                    add_remainder = True

                if collect_init:
                    match = re.compile( r"^\w+\-\d+\-\w+\s\d+").match(line)
                    if match is not None:
                        lines.append({
                            'data': match.group(),
                            'type': 'section',
                        })
                    else:
                        course_pattern = re.compile(r"^[A-Z]+ TOTAL: \d+")
                        course_match = course_pattern.match(line)
                        if course_match is not None:
                            lines.append({
                                'data': course_match.group(),
                                'type': 'total',
                            })
                elif add_remainder:
                    if on_index == len(lines): on_index = 0
                    _lines = line.split("  ")
                    for item in _lines:
                        if '%' in item: continue
                        remainder = re.compile(r"^ \d+").match(item)
                        if remainder is not None:
                            try:
                                lines[on_index]['data'] += remainder.group().rstrip()
                            except:
                                print("howdy")

                            on_index += 1
                elif add_end:
                    _lines = line.replace("Error", '0.000').strip().split("  ")
                    for part in _lines:
                        if on_index == len(lines): on_index = 0

                        type = lines[on_index]['type']

                        if type == 'section':
                            matches = re.compile(r"\d+ \d\.\d+ \d+ \d+ \d+ \d+ \d+ \d+ [\w+\s]*").match(part.strip())
                        elif type == 'total':
                            matches = re.compile(r"\d+ \d\.\d+ \d+ \d+ \d+ \d+ \d+ \d+").match(part.strip())
                        else:
                            continue

                        if matches is not None:
                            lines[on_index]['data'] += (" " + matches.group())
                        else:
                            print("problem")

                        on_index += 1

        new_data += lines



    # WE IGNORE THE TOTAL TYPES BECAUSE WE ONLY CARE ABOUT SECTIONS
    # ONCE HERE IT HAS TRANSFORMED THE FILE. NOW WE JUST NEED TO PUT THE PROFESSOR NAMES ON A NEW LINE AND THEN
    # JUST RUN THE OLD FUNCTIONS ON IT.

    _transformed_list = []

    # go through all the data we've collected
    for index, row in enumerate(new_data):
        if row['type'] == 'section':
            # only operate on the sections for the professors
            # try to find the name
            professor = re.compile(r"[A-Z]+\s[A-Z]+$").search(row['data'])
            if professor is None:
                continue
                # if we don't just skip
            else:
                professor = professor.group()

            # we will feed into the master dictionary a list that will have all course data on row A and the professor name on row B
            _transformed_list.append(row['data'].replace(professor, "").strip())
            _transformed_list.append(professor)

    # NOW NEW TRANSFORMED STRING IS IN THE CORRECT FORMAT
    return getCoursesWithProfessorsTransformed(_transformed_list)