from createMasterDB import createMasterDBs
from downloadPDFs import downloadPDFs
from googleOCR import googleOCR
from manipulatePDFs import manipulatePdfs
from outputData import outputData
from openpyxl import Workbook
import os
from os import path

from glob import glob

_author_ = "Marcus Salinas"


def find_ext(dr, ext):
    return glob(path.join(dr, "*.{}".format(ext)))


def getSemesterChar(semester):
    if semester == "Spring":
        return "A"
    elif semester == "Summer":
        return "B"
    elif semester == "Fall":
        return "C"
    else:
        return "N/A"

def semesterCharToURLChar(semesterChar):
    if semesterChar == "A":
        return "1"
    elif semesterChar == "B":
        return "2"
    elif semesterChar == "C":
        return "3"
    else:
        return "0"

# url = "http://web-as.tamu.edu/gradereport/PDFReports/"
url = "http://web-as.tamu.edu/gradereports/"
listOfColleges = [
    "AE",  # ACADEMIC SUCCESS CENTER
    "AG",  # AGRICULTURE AND LIFE SCIENCES
    "AR",  # ARCHITECTURE
    "AP",  # ASSOCIATE PROVOST FOR UNDERGRADUATE PROGRAMS
    "BA",  # BUSINESS
    "DN",  # DENTISTRY (UNDERGRADUATE & GRADUATE)
    "DN_PROF",  # DENTISTRY (PROFESSIONAL)
    "ED",  # EDUCATION Spring 2016
    "EN",  # ENGINEERING
    "GB",  # GEORGE BUSH SCHOOL OF GOVERNMENT
    "GE",  # GEOSCIENCES
    "SL",  # SCHOOL OF LAW (UNDERGRADUATE & GRADUATE)
    "SL_PROF",  # SCHOOL OF LAW (PROFESSIONAL)
    "LA",  # LIBERAL ARTS Spring 2014
    "MD", # MEDICINE (UNDERGRADUATE & PROFESSIONAL)
    "MD_PROF",  # MEDICINE (UNDERGRADUATE & PROFESSIONAL)
    "MS",  # MILITARY SCIENCE
    "NU",  # NURSING
    "CP_PROF",  # PHARMACY (PROFESSIONAL)
    "PH",  # PUBLIC HEALTH
    "SC",  # SCIENCE
    "VM",  # VETERINARY MEDICINE (UNDERGRADUATE & GRADUATE)
    "VM_PROF",  # VETERINARY MEDICINE (PROFESSIONAL)
]

listOfSemesters = [
     "Spring",  # A
     # "Summer",  # B
     # "Fall"  # C
]

years = [
    # 2012,
    # 2013,
    # 2014,
    # 2015,
    # 2016,
    # 2017,
    # 2018,
    # 2019,
    2020
]
MainDirectory = os.getcwd()
for year in years:
    for semester in listOfSemesters:
        print ("On Semester: " + semester)
        os.chdir(MainDirectory)
        semesterChar = getSemesterChar(semester)
        folderName = semester + str(year)
        pdfFileDirectory = os.path.join(os.getcwd(),"GradeDistributionsDB",folderName)
        yearAndURLChar = str(year) + semesterCharToURLChar(semesterChar)
        # Part 1a
        # get the data from the website
        for x in range(0, len(listOfColleges)):
            print("On College: " + str(listOfColleges[x]))
            downloadPDFs(url, str(year), semesterChar, listOfColleges[x])

        os.chdir(pdfFileDirectory)
        # # # Part 1b
        # # take the pdfs and make them to text files
        # pdfList = glob('*.pdf')
        # googleOCR(folderName, pdfList)

        # Part 2a
        # take all the data we have right now and give us what we need
        txtList = glob('*.txt')
        for textFile in txtList:
            os.chdir(MainDirectory)
            print ("On TextFile " + textFile)
            college = textFile[8:10]
            masterDictionary = manipulatePdfs(textFile, semester, str(year))
        # #
        # #     # Part 2b
        # #     # take the data we have and make it useful
        #     title = semester + str(year) + " " + college + ".xlsx"
        #     wb = Workbook()
        #
        # #     # save the file to a new path
        #     newPath = os.getcwd() + "\\Output"
        #     if not os.path.exists(newPath):
        #         os.makedirs(newPath)
        #     os.chdir(newPath)
        #
        # #     # call the function to outpt data and save in the new path
        #     wb = outputData(masterDictionary, title)
        #     wb.save(title)

# finally we just run the createMaster DB file
os.chdir(MainDirectory)
createMasterDBs(listOfColleges)
