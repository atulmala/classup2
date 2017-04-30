import MySQLdb
import json
import urllib, urllib2

print('Starting to send bulk sms')

# 29/01/17 - values for msg91 vendor
authkey = '138436Aff1HY1Vurw588743cf'
rout = 'default'

try:
    # connect to the database
    db = MySQLdb.connect('classup-prod-1-aurora-cluster.cluster-ceglypsnyux3.us-west-2.rds.amazonaws.com',
                         'classup', 'classup', 'classup2')
    cursor1 = db.cursor()

    # extract the list of all sms for which api_called = false
    sql1 = "select id, sender_code, recipient_number, message from operations_smsrecord " \
           "where api_called = 0 and message_type = 'Bulk SMS (Web Interface)'"
    cursor1.execute(sql1)

    # send messages one by one
    row = cursor1.fetchone()
    while row is not None:
        id = row[0]
        sender_id = row[1]
        mobile = row[2]
        message = row[3]

        values = {
            'authkey': authkey,
            'mobiles': mobile,
            'message': message,
            'sender': sender_id,
            'rout': rout,
            'response': 'json',
        }
        url = 'https://control.msg91.com/api/sendhttp.php'
        print(url)
        postdata = urllib.urlencode(values)

        try:
            print('sending to=' + mobile)
            print('message received in send_bulk_sms.py=' + message)

            # 09/02/17 - old vendor (SMPPSMS Hub) credits exhausted. Turning on new vendor msg91's api
            req = urllib2.Request(url, postdata)
            response = urllib2.urlopen(req)
            j = json.loads(response.read())
            message_id = j['message']
            print(message_id)
            print('status (job_id) = ' + message_id)

            # update the smsrecord table that this message has been sent
            try:
                cursor2 = db.cursor()
                sql2 = "UPDATE operations_smsrecord SET api_called = 1, outcome ='" + message_id
                sql2 += "' WHERE id=" + str(id)
                print(sql2)
                cursor2.execute(sql2)
                db.commit()
                cursor2.close()
            except Exception as e:
                print('Error while trying to update the delivery status of sms with message_id = ' + message_id)
                print ('Exception3 from operations get_sms_dlvry_status.py = %s (%s)' % (e.message, type(e)))
        except Exception as e:
            print ('Exception1 from send_bulk_sms.py = %s (%s)' % (e.message, type(e)))
            print('failed to send message: ' + message + ' to mobile number: ' + str(mobile))
        row = cursor1.fetchone()

    cursor1.close()
    db.close()
except Exception as e:
    print('Error 2 from send_bulk_sms.py')
    print('Exception2 from send_bulk_sms.py = %s (%s)' % (e.message, type(e)))
