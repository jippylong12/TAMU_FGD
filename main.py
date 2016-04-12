_author_ = "Marcus Salinas"

from downloadPDFs import downloadPDFs
from manipulatePDFs import manipulatePdfs
from outputData import outputData
from openpyxl import Workbook
import os

url = "http://web-as.tamu.edu/gradereport/"

listOfColleges = [
    "AG", # AGRICULTURE AND LIFE SCIENCES
    "AR", # ARCHITECTURE
    "BA", # BUSINESS ADMINISTRATION
    "ED", # EDUCATION
    "EL", # ENGLISH LANGUAGE INSTITUTE
    "EN", # ENGINEERING
    "GB", # GEORGE BUSH SCHOOL OF GOVERNMENT
    "GE", # GEOSCIENCES
    "LA", # LIBERAL ARTS
    "MD", # MEDICINE
    "MS", # MILITARY SCIENCE
    "SC", # SCIENCE
    "VM"  # VETERINARY MEDICINE
]

listOfSemesters = [
    "A", # Spring
    "B", # Summer
    "C"  # Fall
]

semester = "Fall"
year = 2015

# Part 1
# get the data from the website
#for x in xrange(0,len(listOfColleges)):
    #print "On College: " + str(listOfColleges[x])
    #downloadPDFs(url,str(year),"C",listOfColleges[x])

# Part 2
# take all the data we have right now and give us what we need
file = 'grd20153EN.txt'
college = "Engineering"
masterDictionary = manipulatePdfs(file)

# Part 3
# take the data we have and make it useful
title = semester+str(year)+ " " + college + ".xlsx"
wb = Workbook()

#save the file to a new path
newPath = os.getcwd() + "\\Output"
if not os.path.exists(newPath):
    os.makedirs(newPath)
os.chdir(newPath)

# call the function to outpt data and save in the new path
wb = outputData(masterDictionary,title)
wb.save(title)


print "Here"