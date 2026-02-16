# used to create teh list of course to be used on the PHP server

import os
from glob import glob
import re

_author_ = "Marcus Salinas"

def create_courses_lists():
    os.chdir(os.getcwd() + "/GradeDistributionsDB/MasterDBs")

    csvList = glob("*.csv")
    for csv in csvList:
        courseList = []
        with open(csv, 'r') as csvFile:
            textName = csv.replace("MasterDB.csv", "CoursesList.txt")
            with open(textName, 'w') as textFile:
                for line in csvFile:
                    foundCourse = re.match("\w+-\d+", line)
                    try:
                        course = foundCourse.group()[:4]
                        if course not in courseList:
                            courseList.append(course)
                            textFile.write(course + '\n')
                    except:
                        continue