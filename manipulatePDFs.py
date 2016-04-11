_author_ = "Marcus Salinas"

import os
import sys
import re
from collections import defaultdict

# setting up console for encoding
reload(sys)
sys.setdefaultencoding('utf8')

def getDataFromTextFiles(filename):
    filePath = os.getcwd() + "\\GradeDistributionsDB\\Fall2015"
    os.chdir(filePath)
    fileAsList = []
    addData = False
    count = 0

    # we need to go line by line and populate a list in python to hold all the useful data we need. The first filter
    # is by taking only the lines that have useful data. Not sure if this can be used for all files but we'll see.
    with open(filename) as input:
        for line in input: # for each line
            test = line.encode('utf-8')[:5] # we need this to find the start of each section
            if test == "A - F": # start of each section
                addData = True
            if addData: # add data fro this section
                fileAsList.append(line.encode('utf-8'))
                count += 1
                if count == 32: # once we get to 32 we've gotten to the end of the section
                    addData = False # stop counting
                    count = 0 # reset for next section

    return fileAsList

def getCoursesWithProfessors(usefulData):
    listOfCourses = []
    listOfProfessors = []
    masterDictionary = defaultdict(list)

    currentCourse = ""
    tempCourseInfo = ""

    for line in usefulData:
        if line[:6] == "COURSE":
            continue
        foundCourseMatch = re.search("\w+-\d+-\d+ \d+ \d+ \d+ \d+ \d+ \d+ \d.\d+",line)
        if foundCourseMatch != None:
            tempCourseInfo = foundCourseMatch.group()
            currentCourse = tempCourseInfo[:8]
        foundProfessor = re.match("[A-Z]+ [A-Z]",line)
        if foundProfessor != None and line[:5] != "A - F":
            masterDictionary[currentCourse].append((tempCourseInfo,foundProfessor.group()))

    return masterDictionary

def manipulatePdfs(file):
    usefulData = getDataFromTextFiles(file)

    masterDictionary = getCoursesWithProfessors(usefulData)

    return masterDictionary
