import MySQLdb
import urllib

print('Starting to extract sms delivery status')
# 30/04/2017 - values for softsms vendor
key = '58fc1def26489'

try:
    # connect to the database
    db = MySQLdb.connect('classup-prod-1-aurora-cluster.cluster-ceglypsnyux3.us-west-2.rds.amazonaws.com',
                         'classup', 'classup', 'classup2')
    cursor3 = db.cursor()
    print ('cursor3=')
    print (cursor3)
    sql3 = "select status from teacher_messagereceivers where status_extracted = 0 and date > '2017-11-28' and date < DATE_SUB(NOW(), INTERVAL 3 HOUR);"
    print ('sql3 = %s' % sql3)
    cursor3.execute(sql3)
    print ('cursor3 executed')
    row3 = cursor3.fetchone()
    print ('row3=')
    print(row3)
    while row3 is not None:
        print ('reached point K2')
        message_id = row3[0]
        print ('message_id = %s' % message_id)
        if message_id:
            print(message_id)
            outcome = 'Status Awaited'
            try:
                url = 'http://softsms.in/app/miscapi/'
                url += key
                url += '/getDLR/'
                url += str(message_id)
                print('url=%s' % url)

                response = urllib.urlopen(url)
                outcome = response.read()
                print('status = ')
                print (outcome)
            except Exception as e:
                print('unable to get the staus of sms delivery. The url was: ')
                print(url)
                print ('Exception 30112017-A from operations get_sms_dlvry_status.py = %s (%s)' % (e.message, type(e)))
            # update the smsrecord table that the delivery status of this sms has been extracted, hence no need
            # to extract its delivery status when this program runs the next time
            try:
                cursor4 = db.cursor()
                sql4 = "UPDATE teacher_messagereceivers SET status_extracted=1, outcome='" + outcome
                sql4 += "' WHERE status='" + message_id + "'"
                print(sql4)
                cursor4.execute(sql4)
                db.commit()
                cursor4.close()
            except Exception as e:
                print('Error while trying to update the delivery status of sms with message_id = ' + message_id)
                print ('Exception3 from operations get_sms_dlvry_status.py = %s (%s)' % (e.message, type(e)))
        row3 = cursor3.fetchone()
    db.close()
except Exception as e:
    db.close()
    print('Error 1 from get_sms_delivery_status.py')
    print('Exception1 from get_sms_dlvry_status.py = %s (%s)' % (e.message, type(e)))
