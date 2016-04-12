_author_ = "Marcus Salinas"

from openpyxl import Workbook
from collections import defaultdict

def outputData(masterDictionary,title):
    wb = Workbook()
    ws = wb.active

    ws.cell(row = 1, column =1).value = "Course"
    ws.cell(row = 1, column = 2).value = "Professor"
    ws.cell(row = 1, column = 3).value = "GPA"
    ws.cell(row = 1, column = 4).value = "# of A's"
    ws.cell(row = 1, column = 5).value = "# of B's"
    ws.cell(row = 1, column = 6).value = "# of C's"
    ws.cell(row = 1, column = 7).value = "# of D's"
    ws.cell(row = 1, column = 8).value = "# of F's"

    rowCount = 2

    #'{:.1%}'.format(1/3.0)


        # writing class data to spreadsheet






    return wb

