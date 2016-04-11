_author_ = "Marcus Salinas"


from selenium import webdriver
import os
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

def createPrettyFilePath(college,semester):
    #colleges
    if college == "AG":
        newCollege = "AGRICULTURE AND LIFE SCIENCES"
    elif college == "AR":
        newCollege = "ARCHITECTURE"
    elif college == "BA":
        newCollege = "BUSINESS ADMINISTRATION"
    elif college == "ED":
        newCollege = "EDUCATION"
    elif college == "EL":
        newCollege = "ENGLISH LANGUAGE INSTITUTE"
    elif college == "EN":
        newCollege = "ENGINEERING"
    elif college == "GB":
        newCollege = "GEORGE BUSH SCHOOL OF GOVERNMENT"
    elif college == "GE":
        newCollege = "GEOSCIENCES"
    elif college == "LA":
        newCollege = "LIBERAL ARTS"
    elif college == "MD":
        newCollege = "MEDICINE"
    elif college == "MS":
        newCollege = "MILITARY SCIENCE"
    elif college == "SC":
        newCollege = "SCIENCE"
    elif college == "VM":
        newCollege = "VETERINARY MEDICINE"
    else:
        newCollege = "N/A"

    #semester
    if semester == "A":
        newSemester = "Spring"
    elif semester == "B":
        newSemester = "Summer"
    elif semester == "C":
        newSemester = "Fall"
    else:
        newSemester = "N/A"

    if newCollege != "N/A" and newSemester != "N/A":
        return (newCollege,newSemester)
    else:
        return (0,0)

def downloadPDFs(url,year,semester,college):

    #set up firefox profile
    fp = webdriver.FirefoxProfile()

    # go to where we downloaded project and create initial DB folder
    downloadFilesHere = os.getcwd()
    downloadFilesHere = downloadFilesHere + "\\GradeDistributionsDB"
    if not os.path.exists(downloadFilesHere):
        os.chdir(downloadFilesHere)

    # create a new folder for each different semester
    filePathCollege,filePathSemester = createPrettyFilePath(college,semester)
    downloadFilesHere = downloadFilesHere + "\\" +str(filePathSemester) + str(year) + " - " + str(filePathCollege)
    if not os.path.exists(downloadFilesHere):
        os.makedirs(downloadFilesHere)

    fp.set_preference("browser.download.folderList",2)
    fp.set_preference("browser.download.manager.showWhenStarting",False)
    fp.set_preference("browser.download.dir", downloadFilesHere)
    fp.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")


    #set up firefox
    driver = webdriver.Firefox(firefox_profile=fp)
    driver.get(url)

    # select the right year
    yearELEM = driver.find_element_by_id("ctl00_plcMain_lstGradYear")
    yearSELECT = Select(yearELEM)
    yearSELECT.select_by_value(year)

    # select the correct semester
    semesterELEM = driver.find_element_by_id("ctl00_plcMain_lstGradTerm")
    semesterSELECT = Select (semesterELEM)
    semesterSELECT.select_by_value(semester)

    # select the correct college i.e ENGINEERING
    collegeELEM = driver.find_element_by_id("ctl00_plcMain_lstGradCollege")
    collegeSELECT = Select(collegeELEM)
    collegeSELECT.select_by_value(college)

    #find and click download button



    #elem.send_keys(Keys.ARROW_DOWN)