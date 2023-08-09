from __future__ import print_function
from selenium import webdriver
import os
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

_author_ = "Marcus Salinas"


def create_filepath(semester):

    # semester
    if semester == "A":
        new_semester = "Spring"
    elif semester == "B":
        new_semester = "Summer"
    elif semester == "C":
        new_semester = "Fall"
    else:
        new_semester = "N/A"

    if new_semester != "N/A":
        return new_semester
    else:
        return 0


def downloadPDFs(url, year, semester, college):
    driver, filepath = setup_driver(semester, year)
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

    fileends = "crdownload"
    while "crdownload" == fileends:
        time.sleep(1)
        newest_file = latest_download_file(filepath)
        if "crdownload" in newest_file:
            fileends = "crdownload"
        else:
            fileends = "none"
    # exit
    time.sleep(10)  # wait to download
    driver.quit()


def setup_driver(semester, year):
    # go to where we downloaded project and create initial DB folder
    download_filepath = os.getcwd() + "\\GradeDistributionsDB"
    if not os.path.exists(download_filepath):
        os.chdir(download_filepath)

    # create a new folder for each different semester
    semester_filepath = create_filepath(semester)
    download_filepath = download_filepath + \
                        "\\" + str(semester_filepath) + str(year)
    if not os.path.exists(download_filepath):
        os.makedirs(download_filepath)

    options = webdriver.ChromeOptions()

    profile = {"plugins.always_open_pdf_externally": True,  # Disable Chrome's PDF Viewer
               "download.default_directory": download_filepath, "download.extensions_to_open": "applications/pdf"}
    options.add_experimental_option("prefs", profile)
    return (webdriver.Chrome('C:\\SeleniumDrivers\chromedriver.exe',
                            chrome_options=options), download_filepath)


def latest_download_file(filepath):
    old_dir = os.getcwd()
    os.chdir(filepath)
    files = sorted(os.listdir(filepath), key=os.path.getmtime)
    newest = files[-1]
    os.chdir(old_dir)
    return newest
