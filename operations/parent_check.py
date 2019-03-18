import xlrd
import MySQLdb
import urllib

loc = ("/Users/atul/classup/classup/operations/data/jps_parents.xlsx")

wb = xlrd.open_workbook(loc)
sheet = wb.sheet_by_index(0)

# db = MySQLdb.connect('35.194.43.14', 'classup', 'classup', 'classup2')
db = MySQLdb.connect('127.0.0.1', 'classup', 'classup', 'classup2')
cursor1 = db.cursor()

for row in range(sheet.nrows):
    if row == 0:
        continue
    print ('Processing a new row')
    parent_id = sheet.cell(row, 0).value

    print(old_erp_id)
    new_erp_id = sheet.cell(row, 2).value

    sql2 = "UPDATE student_student SET student_erp_id='%s' WHERE student_erp_id ='%s' and school_id=20" % (new_erp_id, old_erp_id)
    print(sql2)
    cursor1.execute(sql2)
    db.commit()
cursor1.close()