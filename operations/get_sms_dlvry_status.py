import MySQLdb

print('Starting to extract sms delivery status')

try:
    db = MySQLdb.connect('classup-prod-1-aurora-cluster.cluster-ceglypsnyux3.us-west-2.rds.amazonaws.com',
                         'classup', 'classup', 'classup2')
    cursor = db.cursor()
    cursor.execute('SELECT VERSION()')
    data = cursor.fetchone()
    print('Database version is %s ' % data)

    sql = 'select outcome, status_extracted, status from operations_smsrecord where status_extracted='
    cursor.execute(sql)
    row =cursor.fetchone()

    print(row)
    db.close()
except Exception as e:
    print('Error 1 from get_sms_delivery_status.py')
    print('Exception3 from sms.py = %s (%s)' % (e.message, type(e)))