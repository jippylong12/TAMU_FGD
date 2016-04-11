_author_ = "Marcus Salinas"

from dowloadPDFs import downloadPDFs

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

for x in xrange(0,len(listOfColleges)):
    print "On College: " + str(listOfColleges[x])
    downloadPDFs(url,str(2015),"C",listOfColleges[x])

