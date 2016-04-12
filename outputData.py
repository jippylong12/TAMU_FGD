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

    #writing class data to spreadsheet if not using sortByCourse Method
    for courseName,dataList in masterDictionary.items():
        ws.cell(row = rowCount, column = 1).value = courseName
        rowCount += 1
        for item in dataList:
            professorName = item.keys()[0]
            ws.cell(row = rowCount, column = 2).value = professorName
            ws.cell(row = rowCount, column = 3).value = item[professorName][13]
            ws.cell(row = rowCount, column = 4).value = '{:.2%}'.format(item[professorName][8])
            ws.cell(row = rowCount, column = 5).value = '{:.2%}'.format(item[professorName][9])
            ws.cell(row = rowCount, column = 6).value = '{:.2%}'.format(item[professorName][10])
            ws.cell(row = rowCount, column = 7).value = '{:.2%}'.format(item[professorName][11])
            ws.cell(row = rowCount, column = 8).value = '{:.2%}'.format(item[professorName][12])
            rowCount += 1
        rowCount+=1


    print "Here"



    return wb

