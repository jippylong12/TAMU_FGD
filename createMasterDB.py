# takes all the output files and creates a masterDB through all semester
# for each of the Schools.

from openpyxl import load_workbook
import os
from collections import defaultdict
import collections
import csv

_author_ = "Marcus Salinas"


def createMasterDBs(listOfColleges):
    mainDirectory = os.getcwd() + '/GradeDistributionsDB'
    outputDirectory = mainDirectory + '/MasterDBs'
    if not os.path.exists(outputDirectory):
        os.makedirs(outputDirectory)

    os.chdir(mainDirectory)
    listOfFolders = next(os.walk('.'))[1]
    listOfFolders.remove('MasterDBs')
    for college in listOfColleges:
        masterDB = defaultdict(dict)

        # create the master DB dictirionary
        for folder in listOfFolders:
            os.chdir(os.getcwd() + '/' + folder + '/Output')
            currentWBName = folder + ' ' + college + '.xlsx'
            print ("Starting " + currentWBName)
            wb = load_workbook(currentWBName, read_only=True)
            ws = wb.active
            currentCourse = ''
            for rownum, row in enumerate(ws.rows):
                print(rownum, row[0].value)
                # skip the first row
                if rownum == 0:
                    continue
                # check for the course name
                if row[0].value is not None:
                    currentCourse = row[0].value.encode('utf-8')
                    # if not in the master Dcit we add it
                    if currentCourse not in masterDB:
                        masterDB[currentCourse] = defaultdict(list)
                if row[1].value is not None:
                    # create the list of grades
                    if row[1].value.encode('utf-8') not in masterDB[currentCourse]:
                        # need 8 values, the GPA, 5 percentages A-F, q drops,
                        # and a count
                        masterDB[currentCourse][row[1].value.encode(
                            'utf-8')] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

                    # GPA
                    masterDB[currentCourse][row[1].value.encode(
                        'utf-8')][0] += float(row[2].value)

                    # grade percentages A,B,C,D,F
                    masterDB[currentCourse][row[1].value.encode(
                        'utf-8')][1] += float(row[3].value.replace("%", ''))
                    masterDB[currentCourse][row[1].value.encode(
                        'utf-8')][2] += float(row[4].value.replace("%", ''))
                    masterDB[currentCourse][row[1].value.encode(
                        'utf-8')][3] += float(row[5].value.replace("%", ''))
                    masterDB[currentCourse][row[1].value.encode(
                        'utf-8')][4] += float(row[6].value.replace("%", ''))
                    masterDB[currentCourse][row[1].value.encode(
                        'utf-8')][5] += float(row[7].value.replace("%", ''))
                    # q drops
                    masterDB[currentCourse][row[1].value.encode(
                        'utf-8')][6] += float(row[8].value.replace("%", ''))
                    # the count
                    masterDB[currentCourse][
                        row[1].value.encode('utf-8')][7] += 1

            os.chdir(mainDirectory)
            print ("done with" + currentWBName)

        # output to csv file
        headerLine = ['Course', 'Professor', 'GPA', '% of A\'s', '% of B\'s',
                      '% of C\'s', '% of D\'s', '% of F\'s', '% of Q Drop\'s',
                      'N']
        blankLine = ['', '', '', '', '', '', '', '', '']
        csvFileName = college + 'MasterDB.csv'
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
                    spamwriter.writerow(['', teacher,
                                         round(thisTeacherList[
                                             0] / thisTeacherList[7], 2),
                                         str(thisTeacherList[
                                             1] / thisTeacherList[7]) + '%',
                                         str(thisTeacherList[
                                             2] / thisTeacherList[7]) + '%',
                                         str(thisTeacherList[
                                             3] / thisTeacherList[7]) + '%',
                                         str(thisTeacherList[
                                             4] / thisTeacherList[7]) + '%',
                                         str(thisTeacherList[
                                             5] / thisTeacherList[7]) + '%',
                                         str(thisTeacherList[
                                             6] / thisTeacherList[7]) + '%',
                                         str(thisTeacherList[7])])
                # output blank row
                spamwriter.writerow(blankLine)
        os.chdir(mainDirectory)
