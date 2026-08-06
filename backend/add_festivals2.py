import openpyxl
from datetime import datetime

file_path = 'data/Farm_Booking_Data_new.xlsx'
wb = openpyxl.load_workbook(file_path)
if 'Sheet4' in wb.sheetnames:
    ws = wb['Sheet4']
    ws.append(['Makar Sankranti', datetime(2027, 1, 14), datetime(2027, 1, 13, 17, 0, 0), datetime(2027, 1, 15, 17, 0, 0)])
    wb.save(file_path)
    print("Added Makar Sankranti 2027 to Sheet4 safely.")
else:
    print("Sheet4 not found")
