from pypdf import PdfReader

reader = PdfReader("GradeDistributionsDB/Spring2020/grd20201SC.pdf")
number_of_pages = len(reader.pages)
page = reader.pages[0]
text = page.extract_text()
