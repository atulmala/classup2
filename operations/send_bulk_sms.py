import MySQLdb
import urllib

print('Starting to send bulk sms')

# 30/04/2017 - values for softsms vendor
key = '58fc1def26489'

try:
    # connect to the database
    try:
        db = MySQLdb.connect('35.194.43.14', 'classup', 'classup', 'classup2')
        cursor1 = db.cursor()

        # extract the list of all sms for which api_called = false
        sql1 = "select id, sender_code, recipient_number, message from operations_smsrecord " \
               "where api_called = 0 and message_type = 'Bulk SMS (Web Interface)'"
        cursor1.execute(sql1)
    except Exception as e:
        print('exception 29032018-A from send_bulk_sms.py %s (%s)' % (e.message, type(e)))
        print('failed to establish sql connection or executing sql')


    # send messages one by one
    row = cursor1.fetchone()
    while row is not None:
        id = row[0]
        sender_id = row[1]
        mobile = row[2]
        message = row[3]

        m1 = message.replace(" ", "+")
        print(m1)
        m2 = m1.replace("&", "%26")
        print(m2)

        url = 'http://softsms.in/app/smsapi/index.php?'
        url += 'key=%s' % key
        url += '&type=Text'
        url += '&contacts=%s' % mobile
        url += '&senderid=%s' % sender_id
        url += '&msg=%s' % m2
        print('url=%s' % url)
        print(url)

        try:
            print('sending to=' + mobile)
            print('message received in send_bulk_sms.py=' + message)

            response = urllib.urlopen(url)
            print('response = ')
            message_id = response.read()
            print(message_id)

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
                print ('Exception3 from operations get_sms_dlvry_status.py = %s (%s) %s' % (e.message, type(e), e.args))
        except Exception as e:
            print ('Exception1 from send_bulk_sms.py = %s (%s)' % (e.message, type(e)))
            print('failed to send message: ' + message + ' to mobile number: ' + str(mobile))

        row = cursor1.fetchone()

    cursor1.close()
    db.close()
except Exception as e:
    print('Error 2 from send_bulk_sms.py')
    print('Exception2 from send_bulk_sms.py = %s (%s)' % (e.message, type(e)))
