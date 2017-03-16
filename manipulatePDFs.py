import os
import re
from copy import deepcopy
from collections import defaultdict

_author_ = "Marcus Salinas"

# this function will go through the text files
# (after using Google Drive OCR) and remove
# all the unnecessary lines that we don't need.
# It iwill take the lines we do need and add them
# to a list so each item in the list is actually
# a row in the text file


def getDataFromTextFiles(filename, semester, year):
    filePath = os.getcwd() + "/GradeDistributionsDB/" + semester + year
    os.chdir(filePath)
    fileAsList = []
    addData = False

    # we need to go line by line and populate a list in python
    # to hold all the useful data we need. The first filter
    # is by taking only the lines that have useful data. Not
    # sure if this can be used for all files but we'll see.
    with open(filename) as input:
        for line in input:  # for each line
            # we need this to find the start of each section
            test = line[:5]
            if test == "A - F":  # start of each section
                addData = True
            if addData:  # add data fro this section
                if line == '________________':
                    addData = False
                else:
                    fileAsList.append(line)

    return fileAsList

# will look at the text file and based on regex expressions will find the useful course and professor data and make
# a dictionary of list of tuples out of them. The key of the dictionary is the actual course and the touples hold
# the (course info, professor info). It is a list because some courses
# have multiple sections.


def getCoursesWithProfessors(usefulData):

    # setting everything up
    masterDictionary = defaultdict(list)

    currentCourse = ""
    tempCourseInfo = ""

    # for each line use regex to find the course info and professor infor and
    # add them to the master dictionary
    for line in usefulData:
        # skip lines we don't need
        if line[:6] == "COURSE":
            continue
        # find the course it the string. It matches
        # this format of word-digit-...
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
        if (foundProfessor is not None and
            line[:5] != "A - F" and
           (line.find('%') > 0)):
            # add it to the master dictionary
            testString = foundProfessor.group()
            if testString == 'AGRICULTURAL E':
                pass
            masterDictionary[currentCourse].append(
                (tempCourseInfo, foundProfessor.group()))

    return masterDictionary

# take the master Dictionary we have that holds on the information and creates a new dictionary where each entry holds
# the grade distribution by course and professor


def createDataDictionary(masterDictionary):

    masterDataDictionary = defaultdict(list)
    emptyDataList = [
        0,  # As
        0,  # Bs
        0,  # Cs
        0,  # Ds
        0,  # Fs
        0,  # Number Of Students
        0,  # GPA Total
        0,  # Qdrop Count
        0,  # GPA Count
        0,  # Average As
        0,  # Average Bs
        0,  # Average Cs
        0,  # Average Ds
        0,  # Average Fs
        0,  # Average Qdrops
        0   # Average GPA
    ]

    for course, classTouple in masterDictionary.items():
        for Touple in classTouple:
            classProfessor = Touple[1]
            thisTuple = (course, classProfessor)
            if thisTuple not in masterDataDictionary:
                masterDataDictionary[thisTuple].append(deepcopy(emptyDataList))

            # get class data
            classData = Touple[0]
            classData = classData.split(' ')
            classData.pop(0)

            tempClassData = deepcopy(classData)
            # add the data to the totals
            masterDataDictionary[thisTuple][0][0] += float(tempClassData[0])
            masterDataDictionary[thisTuple][0][1] += float(tempClassData[1])
            masterDataDictionary[thisTuple][0][2] += float(tempClassData[2])
            masterDataDictionary[thisTuple][0][3] += float(tempClassData[3])
            masterDataDictionary[thisTuple][0][4] += float(tempClassData[4])
            masterDataDictionary[thisTuple][0][5] += float(tempClassData[5])
            masterDataDictionary[thisTuple][0][6] += float(tempClassData[6])
            masterDataDictionary[thisTuple][0][7] += float(tempClassData[10])
            masterDataDictionary[thisTuple][0][8] += 1

    # now we calculate the averages for each class,professor
    for item in masterDataDictionary:
        # A-F
        masterDataDictionary[item][0][9] = round(masterDataDictionary[item][0][
                                                 0] / masterDataDictionary[item][0][5], 4)
        masterDataDictionary[item][0][10] = round(masterDataDictionary[item][0][
                                                  1] / masterDataDictionary[item][0][5], 4)
        masterDataDictionary[item][0][11] = round(masterDataDictionary[item][0][
                                                  2] / masterDataDictionary[item][0][5], 4)
        masterDataDictionary[item][0][12] = round(masterDataDictionary[item][0][
                                                  3] / masterDataDictionary[item][0][5], 4)
        masterDataDictionary[item][0][13] = round(masterDataDictionary[item][0][
                                                  4] / masterDataDictionary[item][0][5], 4)
        # Q drop
        masterDataDictionary[item][0][14] = round(
            masterDataDictionary[item][0][7] /
            (masterDataDictionary[item][0][7] + masterDataDictionary[item][0][5]), 4)
        # GPA
        masterDataDictionary[item][0][15] = round(masterDataDictionary[item][0][
                                                  6] / masterDataDictionary[item][0][8], 4)

    return masterDataDictionary

# makes a dictionary where the key is the course and the values are a list of dictionaries where those keys are the
# professor and the values is the list of data


def sortByCourse(masterdictionary):
    finalOutputDictionary = defaultdict(list)
    tempDictionary = {}

    for key in masterdictionary.keys():
        tempDictionary[key[1]] = masterdictionary[key][0]
        finalOutputDictionary[key[0]].append(deepcopy(tempDictionary))
        tempDictionary.clear()

    return finalOutputDictionary


def manipulatePdfs(file, semester, year):
    # get the data
    usefulData = getDataFromTextFiles(file, semester, year)

    # filter the data to only the data we need
    masterDictionary = getCoursesWithProfessors(usefulData)
    masterDictionary = createDataDictionary(masterDictionary)
    masterDictionary = sortByCourse(masterDictionary)
    return masterDictionary
