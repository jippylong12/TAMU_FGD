# takes all the output files and creates a masterDB through all semester
# for each of the Schools.

from openpyxl import load_workbook
import os
from collections import defaultdict
import collections
import csv

_author_ = "Marcus Salinas"


# given the data list calculate a GPA
def calculate_GPA(data_list):
    gpa = 0.0
    # A's
    gpa += data_list[1] * 4
    # B's
    gpa += data_list[2] * 3
    # C's
    gpa += data_list[3] * 2
    # D's
    gpa += data_list[4] * 1
    # F's
    gpa += data_list[5] * 0

    # the gpa is the current sum divided by the number of students
    if data_list[7] == 0:
        return 0.0
    else:
        return round(gpa / (data_list[7]), 2)


def createMasterDBs(listOfColleges):
    mainDirectory = os.getcwd() + '/GradeDistributionsDB'
    outputDirectory = mainDirectory + '/MasterDBs'
    if not os.path.exists(outputDirectory):
        os.makedirs(outputDirectory)

    os.chdir(mainDirectory)
    listOfFolders = next(os.walk('.'))[1]
    listOfFolders.remove('MasterDBs')
    masterDB = defaultdict(dict)
    for college in listOfColleges:

        # create the master DB dictirionary
        for folder in listOfFolders:
            currentWBName = folder + ' ' + college + '.xlsx'
            try:
                os.chdir(os.getcwd() + '\\' + folder + '\\Output')
                print("Starting " + currentWBName)
                wb = load_workbook(currentWBName, read_only=True)
                ws = wb.active
                currentCourse = ''
                for rownum, row in enumerate(ws.rows):
                    # skip the first row
                    if rownum == 0:
                        continue
                    # check for the course name
                    if row[0].value is not None:
                        currentCourse = row[0].value
                        # if not in the master Dcit we add it
                        if currentCourse not in masterDB:
                            masterDB[currentCourse] = defaultdict(list)
                    if row[1].value is not None:
                        prof_name = row[1].value.strip()
                        # create the list of grades
                        if prof_name not in masterDB[currentCourse]:
                            # need 8 values, the GPA, 5 percentages A-F, q drops,
                            # and a count
                            masterDB[currentCourse][prof_name] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

                        # GPA
                        masterDB[currentCourse][prof_name][0] += float(row[2].value)

                        course_total = 0
                        # grade percentages A,B,C,D,F
                        masterDB[currentCourse][prof_name][1] += float(row[3].value)
                        course_total += row[3].value
                        masterDB[currentCourse][prof_name][2] += float(row[4].value)
                        course_total += row[4].value
                        masterDB[currentCourse][prof_name][3] += float(row[5].value)
                        course_total += row[5].value
                        masterDB[currentCourse][prof_name][4] += float(row[6].value)
                        course_total += row[6].value
                        masterDB[currentCourse][prof_name][5] += float(row[7].value)
                        course_total += row[7].value
                        # q drops
                        masterDB[currentCourse][prof_name][6] += float(row[8].value)
                        course_total += row[8].value
                        # the count
                        masterDB[currentCourse][
                            prof_name][7] += course_total
                        masterDB[currentCourse][prof_name][8] += 1 # num of semesters

                os.chdir(mainDirectory)
                print("done with " + currentWBName)
            except:
                os.chdir(mainDirectory)
                print("Cannot find: " + currentWBName)
                continue

    # output to csv file
    headerLine = ['Course', 'Professor', 'GPA', '% of A\'s', '% of B\'s',
                  '% of C\'s', '% of D\'s', '% of F\'s', '% of Q Drop\'s',
                  '% of Semesters']
    blankLine = ['', '', '', '', '', '', '', '', '']
    csvFileName = 'MasterDB.csv'
    os.chdir(outputDirectory)
    with open(csvFileName, 'w') as csvfile:
        spamwriter = csv.writer(csvfile)
        spamwriter.writerow(headerLine)
        orderedMasterDB = collections.OrderedDict(sorted(masterDB.items()))
        for course, teachersDict in orderedMasterDB.items():
            # write the course row
            spamwriter.writerow([course, '', '', '', '', '', '', ''])
            # for each teacher output their data
            teachersDict = collections.OrderedDict(
                sorted(teachersDict.items()))
            for teacher in teachersDict:
                thisTeacherList = orderedMasterDB[course][teacher]
                if thisTeacherList[7] == 0:
                    # SOCI 323 has a semester where the parse is 0 or there is an error
                    spamwriter.writerow(['', teacher,
                                         '4.0',
                                         '100%',
                                         '0%',
                                         '0%',
                                         '0%',
                                         '0%',
                                         '0%',
                                         '0%',
                                         str(thisTeacherList[8])])
                else:
                    spamwriter.writerow(['', teacher,
                                         calculate_GPA(thisTeacherList),
                                         str(round(thisTeacherList[
                                                       1] * 100 / thisTeacherList[7], 2)) + '%',
                                         str(round(thisTeacherList[
                                                       2] * 100 / thisTeacherList[7], 2)) + '%',
                                         str(round(thisTeacherList[
                                                       3] * 100 / thisTeacherList[7], 2)) + '%',
                                         str(round(thisTeacherList[
                                                       4] * 100 / thisTeacherList[7], 2)) + '%',
                                         str(round(thisTeacherList[
                                                       5] * 100 / thisTeacherList[7], 2)) + '%',
                                         str(round(thisTeacherList[
                                                       6] * 100 / thisTeacherList[7], 2)) + '%',
                                         str(thisTeacherList[8])])
            # output blank row
            spamwriter.writerow(blankLine)
    os.chdir(mainDirectory)
