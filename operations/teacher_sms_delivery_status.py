import MySQLdb
import urllib

print('Starting to extract sms delivery status')
# 30/04/2017 - values for softsms vendor
key = '58fc1def26489'

try:
    # connect to the database
    # db = MySQLdb.connect('classup-prod-1-aurora-cluster.cluster-ceglypsnyux3.us-west-2.rds.amazonaws.com',
    #                      'classup', 'classup', 'classup2')
    db = MySQLdb.connect('35.194.43.14', 'classup', 'classup', 'classup2')
    cursor3 = db.cursor()
    print ('cursor3=')
    print (cursor3)
    sql3 = "select status from teacher_messagereceivers where status_extracted = 0 and date > '2018-12-01' and date < DATE_SUB(NOW(), INTERVAL 3 HOUR);"
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
                    outcome = status
                    print('status = ' + str(status))
                except Exception as e:
                    print('unable to get the staus of sms delivery. The url was: ')
                    print(url)
                    print ('Exception 23082018-A from operations teacher_sms_dlvry.py = %s (%s)' % (e.message, type(e)))
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
                    outcome = status
                except Exception as e:
                    print('unable to get the staus of sms delivery. The url was: ')
                    print(url)
                    print ('Exception 23082018-B from operations teacker_sms_dlvry.py = %s (%s)' % (e.message, type(e)))
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


