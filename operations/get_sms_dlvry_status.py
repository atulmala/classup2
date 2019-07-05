import MySQLdb
import urllib
import json
print('Starting to extract sms delivery status')
# 30/04/2017 - values for softsms vendor
key = '58fc1def26489'

try:
    #db = MySQLdb.connect('35.194.43.14', 'classup', 'classup', 'classup2')
    db = MySQLdb.connect('127.0.0.1', 'classup', 'classup', 'classup2')
    cursor1 = db.cursor()

    # extract message_id of all the sms sent after 31/01/17 for which sms delivery status has not been extracted
    sql1 = "select outcome, date from operations_smsrecord where api_called = 1 and " \
           "status_extracted = 0 and date > '2019-06-30' and date <= DATE_SUB(NOW(), INTERVAL 3 HOUR)"
    cursor1.execute(sql1)

    # now, try to extract delivery status of each sms by calling api of the bulk sms provider
    status = 'Not Available'
    row = cursor1.fetchone()
    print('row=')
    print(row)
    while row is not None:
        message_id = row[0]
        print(message_id)
        date_sent = row[1]

        the_date = date_sent.strftime('%Y-%m-%d')

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
            print('message was sent using DealSMS API')
            url = 'http://5.9.69.238/reports/getByMid.php?uname=classup&password=56tr43we'
            url += '&sdate=%s' % the_date
            url += '&mid=%s' % message_id

            # now extract the delivery status
            try:
                response = urllib.urlopen(url)
                status = response.read()
                print('delivery status = %s' % status)
            except Exception as e:
                print('exception 02072019-B from get_sms_dlvry_status.py %s %s' % (e.message, type(e)))
                print('failed to extract he delivery status of message with id %s' % message_id)

            # print ('message was sent using SMSGatewayHub api')
            # url = 'https://www.smsgatewayhub.com/api/mt/GetDelivery?APIKey=6ZWRKLTUnEmMMQro3P30SQ&jobid=%s' % \
            #       message_id
            # print(url)
            # try:
            #     response = urllib.urlopen(url)
            #     status = response.read()
            #     j = json.loads(status)
            #     print(j)
            #     status = json.dumps(j['DeliveryReports'][0])
            #
            # except Exception as e:
            #     print('unable to get the staus of sms delivery. The url was: ')
            #     print(url)
            #     print ('Exception 22082018-B from operations get_sms_dlvry_status.py = %s (%s)' % (e.message, type(e)))

        # update the smsrecord table that the delivery status of this sms has been extracted, hence no need
        # to extract its delivery status when this program runs the next time
        try:
            cursor2 = db.cursor()
            sql2 = "UPDATE operations_smsrecord SET status_extracted=1, status='%s'" % status
            sql2 += ' WHERE outcome="%s"' % message_id
            #sql2 += "' WHERE outcome='" + message_id + "'"
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
           "status_extracted = 0 and date > '2019-06-30' and date <= DATE_SUB(NOW(), INTERVAL 3 HOUR)"
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
            print('message was sent using DealSMS API')
            url = 'http://5.9.69.238/reports/getByMid.php?uname=classup&password=56tr43we'
            url += '&sdate=%s' % the_date
            url += '&mid=%s' % message_id

            # now extract the delivery status
            try:
                response = urllib.urlopen(url)
                status = response.read()
                print('delivery status = %s' % status)
            except Exception as e:
                print('exception 02072019-B from get_sms_dlvry_status.py %s %s' % (e.message, type(e)))
                print('failed to extract he delivery status of message with id %s' % message_id)

            # now extract the delivery status
            try:
                response = urllib.urlopen(url)
                status = response.read()
                print('delivery status = %s' % status)
            except Exception as e:
                print('exception 02072019-E from get_sms_dlvry_status.py %s %s' % (e.message, type(e)))
                print('failed to extract he delivery status of message with id %s' % message_id)

            # print ('message was sent using SMSGatewayHub api')
            # url = 'https://www.smsgatewayhub.com/api/mt/GetDelivery?APIKey=6ZWRKLTUnEmMMQro3P30SQ&jobid=%s' % \
            #       message_id
            # print(url)
            # try:
            #     response = urllib.urlopen(url)
            #     status = response.read()
            #     j = json.loads(status)
            #     print(j)
            #     status = json.dumps(j['DeliveryReports'][0])
            #
            # except Exception as e:
            #     print('unable to get the staus of sms delivery. The url was: ')
            #     print(url)
            #     print ('Exception 22082018-B from operations get_sms_dlvry_status.py = %s (%s)' % (e.message, type(e)))

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
