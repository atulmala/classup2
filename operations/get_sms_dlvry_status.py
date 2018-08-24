import MySQLdb
import urllib
import xml.etree.ElementTree as ET

print('Starting to extract sms delivery status')
# 30/04/2017 - values for softsms vendor
key = '58fc1def26489'

try:
    # connect to the database
    db = MySQLdb.connect('classup-prod-1-aurora-cluster.cluster-ceglypsnyux3.us-west-2.rds.amazonaws.com',
                         'classup', 'classup', 'classup2')
    #db = MySQLdb.connect('localhost', 'root', 'kawasaki', 'prod_replica')
    cursor1 = db.cursor()

    # extract message_id of all the sms sent after 31/01/17 for which sms delivery status has not been extracted
    sql1 = "select outcome from operations_smsrecord where api_called = 1 and " \
           "status_extracted = 0 and date > '2018-08-21' and date <= DATE_SUB(NOW(), INTERVAL 3 HOUR)"
    cursor1.execute(sql1)

    # now, try to extract delivery status of each sms by calling api of the bulk sms provider
    status = 'Not Available'
    row = cursor1.fetchone()
    print('row=')
    print(row)
    while row is not None:
        message_id = row[0]
        print(message_id)

        if 'api' in message_id:
            print ('message message was sent using softsms api')
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
        else:
            print ('message was sent using bulksmsleads api')
            url = 'http://sms.bulksmsleads.com/index.php/deliveryapi/smsdelivery/'
            url += '?username=classup&password=classup&smsid='
            url += message_id
            print('url=%s' % url)
            try:
                response = urllib.urlopen(url)
                xml_text = response.read()
                print('xml = ' + xml_text)
                xml = ET.fromstring(xml_text)
                status = ''
                for table in xml.iter('Report'):
                    for child in table:
                        print child.tag, child.text
                        status += child.tag
                        status += ': '
                        status += child.text
                        status += '\n'
                    if 'Invalid' in status:
                        status = 'Not Available'
            except Exception as e:
                print('unable to get the staus of sms delivery. The url was: ')
                print(url)
                print ('Exception 22082018-B from operations get_sms_dlvry_status.py = %s (%s)' % (e.message, type(e)))

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

    # 30/11/2017 - Teachers are also able to see their message history. Fetch the delivery status of each message
    # that appears in the teacher message history
    cursor3 = db.cursor()
    sql3 = "select status from teacher_messagereceivers where " \
           "status_extracted = 0 and date > '2018-08-21' and date <= DATE_SUB(NOW(), INTERVAL 3 HOUR)"
    cursor3.execute(sql3)
    row = cursor3.fetchone()
    print(row)
    while row is not None:
        message_id = row[0]
        print(message_id)
        outcome = 'Status Awaited'
        if 'api' in message_id:
            print ('message message was sent using softsms api')
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
                print ('Exception 22082018-C from operations get_sms_dlvry_status.py = %s (%s)' % (e.message, type(e)))
        else:
            print ('message was sent using bulksmsleads api')
            url = 'http://sms.bulksmsleads.com/index.php/deliveryapi/smsdelivery/'
            url += '?username=classup&password=classup&smsid='
            url += message_id
            print('url=%s' % url)
            try:
                response = urllib.urlopen(url)
                xml_text = response.read()
                print('xml = ' + xml_text)
                xml = ET.fromstring(xml_text)
                status = ''
                for table in xml.iter('Report'):
                    for child in table:
                        print child.tag, child.text
                        status += child.tag
                        status += ': '
                        status += child.text
                        status += '\n'
                    if 'Invalid' in status:
                        status = 'Not Available'
            except Exception as e:
                print('unable to get the staus of sms delivery. The url was: ')
                print(url)
                print ('Exception 22082018-D from operations get_sms_dlvry_status.py = %s (%s)' % (e.message, type(e)))

        # update the smsrecord table that the delivery status of this sms has been extracted, hence no need
        # to extract its delivery status when this program runs the next time
        try:
            cursor4 = db.cursor()
            sql4 = "UPDATE teacher_messagereceivers SET status_extracted=1, outcome='" + outcome
            sql4 += "' WHERE status='" + message_id + "'"
            print(sql4)
            cursor2.execute(sql4)
            db.commit()
            cursor2.close()
        except Exception as e:
            print('Error while trying to update the delivery status of sms with message_id = ' + message_id)
            print ('Exception 4 from operations get_sms_dlvry_status.py = %s (%s)' % (e.message, type(e)))
        row = cursor3.fetchone()

    db.close()
except Exception as e:
    print('Error 1 from get_sms_delivery_status.py')
    print('Exception1 from get_sms_dlvry_status.py = %s (%s)' % (e.message, type(e)))
