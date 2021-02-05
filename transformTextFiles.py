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

    beginningQ = Queue()
    endQ = Queue()

    middleCount = 0
    extraCount = 0
    extraMiddleCount = 0

    middleString = ""
    extraMiddleString = ""

    transformedString = ""

    _list = []
    num_of_courses = 0

    with open(filename) as textFile:
        course_index = 0
        grade_column_index = 0 # we need to go through each column
        starting_courses = False
        grades_data = False
        final_prof_data = False
        final_course_data = False

        for line in textFile:
            if starting_courses:
                if re.match(r"COURSE TOTAL: \d+", line) is not None:
                    _list.append(re.match(r"COURSE TOTAL: \d+", line).group())
                elif re.match(r"DEPARTMENT TOTAL: \d+", line) is not None:
                    _list.append(re.match(r"DEPARTMENT TOTAL: \d+", line).group())
                elif re.match(r"COLLEGE TOTAL: \d+", line) is not None:
                    _list.append(re.match(r"COLLEGE TOTAL: \d+", line).group())
                    grades_data = True
                    starting_courses = False
                elif re.match(r"\w+-\d+-\d+\s\d+", line) is not None:
                    _list.append(re.match(r"\w+-\d+-\d+\s\d+", line).group())
                    num_of_courses += 1
            elif grades_data:
                if re.match("\s\d+\s", line) is not None:
                    number =  re.match("\s\d+\s", line).group().strip()
                    _list[course_index] = _list[course_index] + " " + number
                    course_index += 1
                    if course_index == num_of_courses + 3: # - 1 for the index + 3 because of course, department, college
                        course_index = 0
                        grade_column_index+=1
                        if grade_column_index == 4:
                            grade_column_index = 0
                            course_index = 0
                            final_prof_data = True
                            grades_data = False
            elif final_prof_data:
                if len(re.findall(r"\d+\s\d+\.\d+ \d+ \d+ \d+ \d+ \d+ \d+ \w+ \w", line)) > 0:
                    string_matches = re.findall(r"\d+\s\d+\.\d+ \d+ \d+ \d+ \d+ \d+ \d+ \w+ \w", line)
                    course_index += len(string_matches)
                    for index, elem in  enumerate(string_matches):
                        _list[index] = _list[index] + " " + elem

                    if course_index == num_of_courses:
                        final_prof_data = False
                        final_course_data = True
                        course_index = 0
            elif final_course_data:
                if len(re.findall(r"\d+\s\d+\.\d+ \d+ \d+ \d+ \d+ \d+ \d+", line)) > 0:
                    string_matches = re.findall(r"\d+\s\d+\.\d+ \d+ \d+ \d+ \d+ \d+ \d+", line)
                    for elem in string_matches:
                        _list[num_of_courses + course_index] += " " + elem
                        course_index += 1
            else:
                if re.match(r"\w+-\d+-\d+\s\d+", line) is not None:
                    starting_courses = True
                    _list.append(re.match(r"\w+-\d+-\d+\s\d+", line).group())
                    num_of_courses += 1

    # ONCE HERE IT HAS TRANSFORMED THE FILE. NOW WE JUST NEED TO PUT THE PROFESSOR NAMES ON A NEW LINE AND THEN
    # JUST RUN THE OLD FUNCTIONS ON IT.

    transformedString = ""
    for index, row in enumerate(_list):
        transformedString += row
        if index+1 != len(_list):
            transformedString += "\n\n"



    # NOW NEW TRANSFORMED STRING IS IN THE CORRECT FORMAT
    return getCoursesWithProfessorsTransformed(transformedString)