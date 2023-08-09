from __future__ import print_function
from selenium import webdriver
import os
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

_author_ = "Marcus Salinas"


def createPrettyFilePath(college, semester):
    # colleges
    if college == "AE":
        newCollege = "ACADEMIC SUCCESS CENTER"
    elif college == "AG":
        newCollege = "AGRICULTURE AND LIFE SCIENCES"
    elif college == "AR":
        newCollege = "ARCHITECTURE"
    elif college == "BA":
        newCollege = "BUSINESS"
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

    # semester
    if semester == "A":
        newSemester = "Spring"
    elif semester == "B":
        newSemester = "Summer"
    elif semester == "C":
        newSemester = "Fall"
    else:
        newSemester = "N/A"

    if newCollege != "N/A" and newSemester != "N/A":
        return (newCollege, newSemester)
    else:
        return (0, 0)


def downloadPDFs(url, year, semester, college):
    driver = setup_driver(college, semester, year)
    driver.get(url)

    # select the right year
    year_elem = driver.find_element_by_id("ctl00_plcMain_lstGradYear")
    year_select = Select(year_elem)
    year_select.select_by_value(year)

    # select the correct semester
    semester_elem = driver.find_element_by_id("ctl00_plcMain_lstGradTerm")
    semester_select = Select(semester_elem)
    semester_select.select_by_value(semester)

    # select the correct college i.e ENGINEERING
    college_elem = driver.find_element_by_id("ctl00_plcMain_lstGradCollege")
    college_select = Select(college_elem)
    college_select.select_by_value(college)

    # find and click download button
    download_elem = driver.find_element_by_id("ctl00_plcMain_btnGrade")
    driver.execute_script("arguments[0].click();", download_elem)

    # exit
    time.sleep(5) # wait to download
    driver.quit()


def setup_driver(college, semester, year):
    # go to where we downloaded project and create initial DB folder
    download_filepath = os.getcwd() + "\\GradeDistributionsDB"
    if not os.path.exists(download_filepath):
        os.chdir(download_filepath)

    # create a new folder for each different semester
    _, semester_filepath = createPrettyFilePath(college, semester)
    download_filepath = download_filepath + \
                        "\\" + str(semester_filepath) + str(year)
    if not os.path.exists(download_filepath):
        os.makedirs(download_filepath)

    options = webdriver.ChromeOptions()

    profile = {"plugins.always_open_pdf_externally": True,  # Disable Chrome's PDF Viewer
               "download.default_directory": download_filepath, "download.extensions_to_open": "applications/pdf"}
    options.add_experimental_option("prefs", profile)
    return webdriver.Chrome('C:\\SeleniumDrivers\chromedriver.exe',
                            chrome_options=options)  # Optional argument, if not specified will search path.
