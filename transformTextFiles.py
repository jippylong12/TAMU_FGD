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

def transformedTextFiles(filename, semester, year):
    filePath = os.getcwd() + "/GradeDistributionsDB/" + semester + year
    os.chdir(filePath)

    beginningQ = Queue()
    endQ = Queue()

    middleCount = 0

    middleString = ""

    transformedString = ""

    with open(filename) as textFile:
        for line in textFile:
            if re.match(r"\w+-\d+-\d+\s\d+", line) is not None: # COURSE LINES
                data = re.match(r"\w+-\d+-\d+\s\d+", line).group(0)
                beginningQ.put(data)
            elif re.match(r"\w+\s\w+:\s\d+",line) is not None: # COURSE TOTAL LINE
                data = re.match(r"\w+\s\w+:\s\d+", line).group(0)
                beginningQ.put(data)
            elif re.match(r"\d+\s\d.\d+\s\d+\s\d+\s\d+\s\d+\s\d+\s\d+\s[A-Z-]+[\s[A-Z]{3,}", line): # MORE INFORMATION
                data = re.match(r"\d+\s\d.\d+\s\d+\s\d+\s\d+\s\d+\s\d+\s\d+\s[A-Z-]+[\s[A-Z]{3,}", line)
                data = data.group(0).strip()
                endQ.put(data)

                if middleString != "":
                    transformedString = transformedString + beginningQ.get() + ' ' + middleString + endQ.get() + '\n\n'
                    middleCount =0
                    middleString = ""
            elif re.match(r"\d+\s\d.\d+\s\d+\s\d+\s\d+\s\d+\s\d+\s\d+",line):
                data = re.match(r"\d+\s\d.\d+\s\d+\s\d+\s\d+\s\d+\s\d+\s\d+", line)
                data = data.group(0)
                endQ.put(data)

                if middleString != "":
                    transformedString = transformedString + beginningQ.get() + ' ' + middleString + endQ.get() + '\n\n'
                    middleCount =0
                    middleString = ""
            else: # GET ALL THE MIDDLE STUFF
                if middleCount < 4:
                    if re.match(r"\d+", line) is not None:
                        number = re.match(r"\d+", line)
                        number = number.group(0)
                        middleString = middleString + number + ' '
                        middleCount += 1
                else:
                    continue

    # ONCE HERE IT HAS TRANSFORMED THE FILE. NOW WE JUST NEED TO PUT THE PROFESSOR NAMES ON A NEW LINE AND THEN
    # JUST RUN THE OLD FUNCTIONS ON IT.

    transformedString = transformedString.split("\n")
    newTransformedString = ""
    for line in transformedString:
        try:
            lineOne = re.match(r"\w+-\d+-\d+\s\d+\s\d+\s\d+\s\d+\s\d+\s\d+\s\d+.\d+\s\d+\s\d+\s\d+\s\d+\s\d+\s\d+",line)
            lineOne = lineOne.group(0)
            lineTwo = re.split(r"\w+-\d+-\d+\s\d+\s\d+\s\d+\s\d+\s\d+\s\d+\s\d+.\d+\s\d+\s\d+\s\d+\s\d+\s\d+\s\d+\s",line)
            lineTwo = lineTwo[1]
            newTransformedString = newTransformedString + lineOne + '\n\n' + lineTwo + '\n\n'
        except:
            continue

    newTransformedString = newTransformedString.split('\n\n')
    # NOW NEW TRANSFORMED STRING IS IN THE CORRECT FORMAT
    return getCoursesWithProfessorsTransformed(newTransformedString)
