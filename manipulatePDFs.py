_author_ = "Marcus Salinas"

import os
import sys
import re
from collections import defaultdict

# setting up console for encoding
reload(sys)
sys.setdefaultencoding('utf8')

# this function will go through the text files (after using Google Drive OCR) and remove all the unnecessary lines that
# we don't need. It iwill take the lines we do need and add them to a list so each item in the list is actually
# a row in the text file
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

# will look at the text file and based on regex expressions will find the useful course and professor data and make
# a dictionary of list of tuples out of them. The key of the dictionary is the actual course and the touples hold
# the (course info, professor info). It is a list because some courses have multiple sections.
def getCoursesWithProfessors(usefulData):

    #setting everything up
    listOfCourses = []
    listOfProfessors = []
    masterDictionary = defaultdict(list)

    currentCourse = ""
    tempCourseInfo = ""

    # for each line use regex to find the course info and professor infor and add them to the master dictionary
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
    # get the data
    usefulData = getDataFromTextFiles(file)

    # filter the data to only the data we need
    masterDictionary = getCoursesWithProfessors(usefulData)

    return masterDictionary
