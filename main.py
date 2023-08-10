from createCoursesLists import create_courses_lists
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

url = "https://web-as.tamu.edu/gradereports/"
listOfColleges = [
    "AE",  # ACADEMIC SUCCESS CENTER
    "AC",  # ARCHITECTURE
    "AG",  # AGRICULTURE AND LIFE SCIENCES
    "AR",  # ARCHITECTURE
    "AP",  # ASSOCIATE PROVOST FOR UNDERGRADUATE PROGRAMS
    "AT",  # ARTS AND SCIENCES
    "BA",  # MAYS BUSINESS
    "DN",  # DENTISTRY (UNDERGRADUATE & GRADUATE)
    "DN_PROF",  # DENTISTRY (PROFESSIONAL)
    "DT",  # DENTISTRY (UNDERGRADUATE & GRADUATE) NEW
    "DT_PROF",  # DENTISTRY (PROFESSIONAL) NEW
    "ED",  # EDUCATION Spring 2016
    "EN",  # ENGINEERING
    "GB",  # GEORGE BUSH SCHOOL OF GOVERNMENT
    "GE",  # GEOSCIENCES
    "SL",  # SCHOOL OF LAW (UNDERGRADUATE & GRADUATE)
    "SL_PROF",  # SCHOOL OF LAW (PROFESSIONAL)
    "LA",  # LIBERAL ARTS Spring 2014
    "MD", # MEDICINE (UNDERGRADUATE & GRADUATE)
    "MD_PROF",  # MEDICINE (PROFESSIONAL)
    "MN",  # MEDICINE (UNDERGRADUATE & GRADUATE) NEW
    "MN_PROF",  # MEDICINE (PROFESSIONAL) NEW
    "MS",  # MILITARY SCIENCE
    "NS",  # NURSING NEW
    "CP_PROF",  # PHARMACY (PROFESSIONAL)
    "PM_PROF",  # PHARMACY (PROFESSIONAL) NEW
    "PH",  # PUBLIC HEALTH
    "SC",  # SCIENCE
    "VF",  # PERFORMANCE, VISUALIZATION & FINE ARTS
    "VM",  # VETERINARY MEDICINE (UNDERGRADUATE & GRADUATE)
    "VM_PROF",  # VETERINARY MEDICINE (PROFESSIONAL)
    "VT",  # VETERINARY MEDICINE (UNDERGRADUATE & GRADUATE) NEW
    "VT_PROF",  # VETERINARY MEDICINE (PROFESSIONAL) NEW
]

listOfSemesters = [
     "Spring",  # A
     "Summer",  # B
     "Fall"  # C
]

years = [
    # 2018,
    # 2019,
    # 2020,
    2021,
    2022,
]


MainDirectory = os.getcwd()
download_flag = False
for year in years:
    for semester in listOfSemesters:
        print("On Semester: " + semester)
        os.chdir(MainDirectory)
        semesterChar = getSemesterChar(semester)
        folderName = semester + str(year)
        pdfFileDirectory = os.path.join(os.getcwd(),"GradeDistributionsDB",folderName)
        yearAndURLChar = str(year) + semesterCharToURLChar(semesterChar)

        if download_flag:
            # Part 1a
            # get the data from the website
            downloadPDFs(url, str(year), semesterChar, listOfColleges)

            os.chdir(pdfFileDirectory)
            # Part 1b
            # take the pdfs and make them to text files
            pdfList = glob('*.pdf')
            googleOCR(folderName, pdfList)
        else:
            os.chdir(pdfFileDirectory)
            # Part 2a
            # take all the data we have right now and give us what we need
            txtList = glob('*.txt')
            for textFile in txtList:
                os.chdir(MainDirectory)
                print("On TextFile " + textFile)
                college = textFile[8:10]
                masterDictionary = manipulatePdfs(textFile, semester, str(year))

                # Part 2b
                # take the data we have and make it useful
                title = semester + str(year) + " " + college + ".xlsx"
                wb = Workbook()

                # save the file to a new path
                newPath = os.getcwd() + "\\Output"
                if not os.path.exists(newPath):
                    os.makedirs(newPath)
                os.chdir(newPath)

                # call the function to output data and save in the new path
                wb = outputData(masterDictionary, title)
                wb.save(title)


if not download_flag:
    # finally we just run the createMaster DB file
    os.chdir(MainDirectory)
    createMasterDBs(listOfColleges)
    os.chdir(MainDirectory)
    create_courses_lists()
