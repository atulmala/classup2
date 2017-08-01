import MySQLdb
import json
import urllib

print('Starting to extract sms delivery status')
# 30/04/2017 - values for softsms vendor
key = '58fc1def26489'

try:
    # connect to the database
    db = MySQLdb.connect('classup-prod-1-aurora-cluster.cluster-ceglypsnyux3.us-west-2.rds.amazonaws.com',
                         'classup', 'classup', 'classup2')
    cursor1 = db.cursor()

    # extract message_id of all the sms sent after 31/01/17 for which sms delivery status has not been extracted
    sql1 = "select outcome from operations_smsrecord where api_called = 1 and " \
           "status_extracted = 0 and date > '2017-07-30' and date < DATE_SUB(NOW(), INTERVAL 3 HOUR)"
    cursor1.execute(sql1)

    # now, try to extract delivery status of each sms by calling api of the bulk sms provider
    row = cursor1.fetchone()
    print('row=')
    print(row)
    while row is not None:
        message_id = row[0]
        print(message_id)
        status = 'Not Available'
        try:
            url = 'http://softsms.in/app/miscapi/'
            url += key
            url += '/getDLR/'
            url += message_id
            print('url=%s' % url)

            response = urllib.urlopen(url)
            status = response.read()
            print('status = ' + str(status))
        except Exception as e:
            print('unable to get the staus of sms delivery. The url was: ')
            print(url)
            print ('Exception2 from operations get_sms_dlvry_status.py = %s (%s)' % (e.message, type(e)))

        # update the smsrecord table that the delivery status of this sms has been extracted, hence no need
        # to extract its delivery status when this program runs the next time
        try:
            cursor2 = db.cursor()
            sql2 = "UPDATE operations_smsrecord SET status_extracted=1, status='" + status
            sql2 += "' WHERE outcome='" + message_id + "'"
            print(sql2)
            cursor2.execute(sql2)
            db.commit()
            cursor2.close()
        except Exception as e:
            print('Error while trying to update the delivery status of sms with message_id = ' + message_id)
            print ('Exception3 from operations get_sms_dlvry_status.py = %s (%s)' % (e.message, type(e)))
        row = cursor1.fetchone()

    cursor1.close()
    db.close()
except Exception as e:
    print('Error 1 from get_sms_delivery_status.py')
    print('Exception1 from get_sms_dlvry_status.py = %s (%s)' % (e.message, type(e)))
