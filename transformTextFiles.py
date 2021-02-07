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
        course_index = 0
        new_course_index = 0
        grade_column_index = 0 # we need to go through each column

        for line in textFile:
            re_professor = re.findall(r"\d+\s\d+\.\d+ \d+ \d+ \d+ \d+ \d+ \d+ \w+ \w", line)
            re_courses = re.findall(r"\d+\s\d+\.\d+ \d+ \d+ \d+ \d+ \d+ \d+", line)
            re_errors = re.findall('Error', line)
            if len(re_professor) > 0 or len(re_courses) > 0:
                course_index += max(len(re_courses) + len(re_errors) - len(re_professor),0)
                string_matches = re.findall(r"\d+\s\d+\.\d+ \d+ \d+ \d+ \d+ \d+ \d+ \w+ \w", line)
                for index, elem in  enumerate(string_matches):
                    _list[course_index + index] = _list[course_index + index] + " " + elem

                course_index += len(string_matches)
                if course_index == num_of_courses:
                    new_course_index = course_index
            elif re.match("\s\d+\s", line) is not None:
                number =  re.match("\s\d+\s", line).group().strip()
                if course_index < num_of_courses:
                    _list[course_index] = _list[course_index] + " " + number
                course_index += 1
                if course_index == num_of_courses: # - 1 for the index + 3 because of course, department, college
                    course_index = new_course_index
                    grade_column_index+=1
                    if grade_column_index == 4:
                        grade_column_index = 0
                        course_index = new_course_index
            elif re.match(r"\w+-\d+-\d+\s\d+", line) is not None:
                _list.append(re.match(r"\w+-\d+-\d+\s\d+", line).group())
                num_of_courses += 1
            elif re.match(r"COURSE TOTAL: \d+", line) is not None:
                _list.append(re.match(r"COURSE TOTAL: \d+", line).group())
                num_of_courses += 1
            elif re.match(r"DEPARTMENT TOTAL: \d+", line) is not None:
                _list.append(re.match(r"DEPARTMENT TOTAL: \d+", line).group())
                num_of_courses += 1
            elif re.match(r"COLLEGE TOTAL: \d+", line) is not None:
                _list.append(re.match(r"COLLEGE TOTAL: \d+", line).group())
                num_of_courses += 1

    # ONCE HERE IT HAS TRANSFORMED THE FILE. NOW WE JUST NEED TO PUT THE PROFESSOR NAMES ON A NEW LINE AND THEN
    # JUST RUN THE OLD FUNCTIONS ON IT.

    _list = _list[0:num_of_courses]
    _transformed_list = []
    for index, row in enumerate(_list):
        if len(re.findall(r"TOTAL: \d+", row)) == 0:
            if row.startswith("ALEC-425-700"):
                pass
            professor = re.findall(r"\s[A-Z]+ [A-Z]", row)
            if len(professor) == 0:
                continue
            else:
                professor = professor[-1].strip()
            row = row.replace(professor, "").strip()
            _transformed_list.append(row)
            _transformed_list.append(professor)

    # NOW NEW TRANSFORMED STRING IS IN THE CORRECT FORMAT
    return getCoursesWithProfessorsTransformed(_transformed_list)