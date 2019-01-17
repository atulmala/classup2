import json
import datetime
import urllib2
import requests


from ipware.ip import get_ip

from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt

from rest_framework import generics
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.renderers import JSONRenderer
#from push_notifications.models import GCMDevice
#from push_notifications.gcm import gcm_send_message

from setup.models import UserSchoolMapping, GlobalConf
from teacher.models import Teacher
from student.models import Student, Parent
from .models import LoginRecord, LastPasswordReset, user_device_mapping
from .serializers import LogBookSerializer
from operations import sms

from .forms import ClassUpLoginForm


print ('in views.py for authentication')


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class LogEntry(generics.ListCreateAPIView):
    print('inside LogEntry')
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    serializer_class = LogBookSerializer


# 23/07/2017 now we are implementing logging
def log_entry(user, event, category, outcome):
    # 26/11/2018 logs are stored into db and as on date they are more than 2 million. It is not a good practice
    # to store logs in db hence disabling as of now and they will be stored on disk preferably some tool from google
    return
    # print('Inside log_entry')
    # log = {}
    # log['user'] = user
    # log['event'] = event
    # log['category'] = category
    # log['outcome'] = outcome
    # print(log)
    #
    # headers = {'content-type': 'application/json'}
    # global_conf = GlobalConf.objects.get(pk=1)
    # server = global_conf.server_url + 'auth/logbook_entry/'
    # print(server)
    #
    # # get the name of the user. Can be a teacher or parent or admin. Try teacher first
    # try:
    #     t = Teacher.objects.get(email=user)
    #     name = t.first_name + ' ' + t.last_name
    #     print(name)
    #     school = t.school.school_name
    #     log['user_name'] = name
    #     log['school'] = school
    #     print(json.dumps(log))
    #
    #     r = requests.post(server, data=json.dumps(log), headers=headers)
    #     print(r.text)
    #     return
    # except Exception as e:
    #     print('Exception 210 from authentication views.py = %s (%s)' % (e.message, type(e)))
    #     print('will now check to see if this is an Administrator or Parent')
    # # the user is not teacher. Can be are parent or admin
    # try:
    #     u = User.objects.get(username=user)
    #     print('retrieved user')
    #     name = u.first_name + ' ' + u.last_name
    #     log['user_name'] = name
    #     print(name)
    #     if u.is_staff:
    #         print('chances of being and Admin user...')
    #         if u.groups.filter(name='school_admin').exists():
    #             print('user is an admin')
    #             mapping = UserSchoolMapping.objects.get(user=u)
    #             school = mapping.school.school_name
    #             print('school = ' + school)
    #             log['school'] = school
    #             r = requests.post(server, data=json.dumps(log), headers=headers)
    #             print(r.text)
    #             return
    #         else:
    #             print('user is not an admin may be a parent')
    #     else:   # user is parent
    #         print('not a staff. Checking whether parent...')
    #         p = Parent.objects.get(parent_mobile1=user)
    #         q = Student.objects.filter(parent=p, active_status=True).order_by('fist_name')
    #         for s in q:
    #             school = s.school.school_name
    #             break
    #         log['school'] = school
    #         r = requests.post(server, data=json.dumps(log), headers=headers)
    #         print(r.text)
    #         return
    # except Exception as e:
    #     print('user is neither a teacher, nor a parent, nor an administrator. Perhaps a fake user '  )
    #     print('Exception 212 from authentication views.py = %s (%s)' % (e.message, type(e)))
    #     log["user_name"] = "Un-registered User"
    #     log["school"] = "Undetermined"
    #     r = requests.post(server, data=json.dumps(log), headers=headers)
    #     print(r.text)
    #     return


def auth_index(request):
    response = render(request, 'classup/auth_index.html')
    return response

@csrf_exempt
def auth_login(request):
    # we need to record every login attempt into database
    l = LoginRecord()
    l.login_type = 'Web'
    # get the ip address of the user
    ip = get_ip(request)
    if ip is not None:
        print(ip)
        print("we have an IP address for user")
        try:
            l.string_ip = ip
            l.ip_address = ip
            l.save()
        except Exception as e:
            l.string_ip = 'Unable to get'
            l.save()
            print('unable to store ip address')
            print('Exception 1 from authentication views.py = %s (%s)' % (e.message, type(e)))
    else:
        print("we don't have an IP address for user")

    context_dict = {
    }

    if request.method == 'POST':
        #login_form = ClassUpLoginForm(request.POST)
        #context_dict['form'] = login_form
        #user_name = request.POST['username']
        data = json.loads(request.body)
        the_user = data['user']
        log_entry(the_user, "Login from device initiated", "Normal", True)
        password = data['password']
        l.login_id = the_user
        l.password = password
        log_entry(the_user, "Login attempt from web (vuejs)", "Normal", True)
        l.login_id = the_user
        #password = request.POST['password']
        l.password = password

        user = authenticate(username=the_user, password=password)
        log_entry(the_user, "User has been authenticated", "Normal", True)
        if user is not None:
            if user.is_active:
                log_entry(the_user, "User is an Active user", "Normal", True)
                try:
                    login(request, user)
                    l.save()
                    u = UserSchoolMapping.objects.get(user=user)
                    school = u.school
                    request.session['user'] = the_user
                    request.session['school_name'] = school.school_name
                    request.session['school_id'] = school.id
                    context_dict['school_name'] = school.school_name
                    if school.subscription_active:
                        log_entry(the_user, "School subscription found to be Active", "Normal", True)
                        school_id = u.school.id
                        request.session['school_id'] = school_id
                        print ('school_id=' + str(school_id))
                    else:
                        error = school.school_name + "'s subscription has expired. "
                        error += 'Please contact ClassUp support at info@classup.in for renewal'
                        print(error)
                        #login_form.errors['__all__'] = login_form.error_class([error])
                        return render(request, 'classup/auth_login.html', context_dict)
                except Exception as e:
                    print ('unable to retrieve schoo_id for ' + user.username)
                    print('Exception 8 from authentication views.py = %s (%s)' % (e.message, type(e)))
                    log_entry(the_user, "Unable to retrieve School Id. Exception 8 authentication views.py",
                              "Normal", True)
                if user.groups.filter(name='school_admin').exists():
                    log_entry(the_user, "User found to be an Admin User", "Normal", True)
                    context_dict['user_type'] = 'school_admin'
                    request.session['user_type'] = 'school_admin'
                else:
                    log_entry(the_user, "User found to be non-Admin user", "Normal", True)
                    context_dict['user_type'] = 'non_admin'
                    request.session['user_type'] = 'non_admin'
                print (context_dict)
                log_entry(the_user, "Login Successful", "Normal", True)
                return render(request, 'classup/setup_index.html', context_dict)
            else:
                log_entry(the_user, "User is an Inactive user", "Normal", True)
                error = 'User: ' + the_user + ' is disabled. Please contact your administrator'
                l.comments = error
                l.save()
                #login_form.errors['__all__'] = login_form.error_class([error])
                print (error)
                return render(request, 'classup/auth_login.html', context_dict)
        else:
            error = 'Invalid username/password or blank entry. Please try again.'
            l.comments = error
            l.save()
            #login_form.errors['__all__'] = login_form.error_class([error])
            print (error)
            return render(request, 'classup/auth_login.html', context_dict)
    else:
        print('get request')
        login_form = ClassUpLoginForm()
        context_dict['form'] = login_form
    return render(request, 'classup/auth_login.html', context_dict)


def auth_logout(request):
    context_dict = {

    }
    login_form = ClassUpLoginForm()
    context_dict['form'] = login_form
    return render(request, 'classup/auth_login.html', context_dict)


class JSONResponse(HttpResponse):
    """
    an HttpResponse that renders its contents to JSON
    """
    def __init__(self, data, **kwargs):
        print ('from JSONResponse...')
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


@csrf_exempt
def auth_login_from_device1(request):
    event = "Login attempt from device"
    category = "Normal"
    print ('Inside login from device view!')

    l = LoginRecord()
    l.login_type = 'Device'

    # get the ip address of the user
    ip = get_ip(request)
    if ip is not None:
        print(ip)
        print("we have an IP address for user")
        try:
            l.string_ip = ip
            l.ip_address = ip
            l.save()
        except Exception as e:
            l.string_ip = 'Unable to get'
            l.save()
            print('unable to store ip address')
            print('Exception 9 from authentication views.py = %s (%s)' % (e.message, type(e)))
    else:
        print("we don't have an IP address for user")

    return_data = {}

    return_data['school_admin'] = 'false'
    return_data['subscription'] = 'na'
    if request.method == 'POST':
        data = json.loads(request.body)
        the_user = data['user']
        log_entry(the_user, "Login from device initiated", "Normal", True)
        password = data['password']
        l.login_id = the_user
        l.password = password

        # 11/07/2017 we are now capturing the
        try:
            login_type = data['device_type']
            model = data['model']
            os = data['os']
            size = data['size']
            resolution = data['resolution']
            l.login_type = login_type
            l.model = model
            l.os = os
            l.size = size
            l.resolution = resolution
            l.save()
        except Exception as e:
            print ('User %s is still using an older version of app' % the_user)
            print('Exception 250 from authentication views.py = %s (%s)' % (e.message, type(e)))

        print('user trying to login: ' + the_user + ', with password: ' + password)
        user = authenticate(username=the_user, password=password)
        if user is not None:
            print('user ' + the_user + ' has been authenticated')
            log_entry(the_user, "User has been authenticated", "Normal", True)
            if user.is_active:
                print('user ' + the_user + ' is an active user')
                log_entry(the_user, "Found to be an Active User", "Normal", True)
                login(request, user)
                l.outcome = 'Success'
                l.save()
                return_data["login"] = "successful"
                return_data["user_status"] = "active"
                full_name = user.first_name + ' ' + user.last_name
                return_data['user_name'] = full_name
                return_data['welcome_message'] = 'Welcome, ' + full_name

                if user.is_staff:
                    return_data['is_staff'] = "true"

                    # 12/02/17 - checking if this user belong to school_admin group
                    if user.groups.filter(name='school_admin').exists():
                        print('this is a school admin')
                        log_entry(the_user, "User is an Admin User", "Normal", True)
                        return_data["school_admin"] = "true"
                    try:
                        u = UserSchoolMapping.objects.get(user=user)
                        school_id = u.school.id

                        # check whether the subscription of this school is active or not
                        if u.school.subscription_active:
                            return_data['subscription'] = 'active'
                        else:
                            return_data['subscription'] = 'expired'

                        request.session['school_id'] = school_id
                        return_data['school_id'] = school_id
                        print ('school_id=' + str(school_id))
                    except Exception as e:
                        log_entry(the_user,
                                  "School could not be determined. Exception 10 from authentication views.py",
                                  "Normal", True)
                        print ('unable to retrieve school_id for ' + user.username)
                        print('Exception 10 from authentication views.py = %s (%s)' % (e.message, type(e)))
                else:
                    return_data['is_staff'] = "false"
                try:
                    log_entry(the_user, "Login Successful", category, True)
                except Exception as e:
                    print('failed to create log entry for log: ')
                    print('Exception 211 from authentication views.py = %s (%s)' % (e.message, type(e)))
                return JSONResponse(return_data, status=200)
            else:
                l.outcome = 'Failed'
                l.comments = 'Inactive User'
                log_entry(the_user, "Found to be an Inactive User", "Normal", True)
                l.save()
                return_data["login"] = "successful"
                return_data['user_name'] = user.first_name + ' ' + user.last_name
                return_data["user_status"] = "inactive"
                print (return_data)
                log_entry(the_user, event, category, False)
                return JSONResponse(return_data, status=200)
        else:
            l.outcome = 'Failed'
            l.save()
            return_data["login"] = "failed"
            print (return_data)
            log_entry(the_user, "Login Failed", category, False)
            return JSONResponse(return_data, status=200)


@csrf_exempt
def map_device_token(request):
    print('inside map_device_token')
    response_dict = {

    }
    if request.method == 'POST':
        print('request body = ' + request.body)
        data = json.loads(request.body)
        print (data)
        user = data['user']
        print('user = ' + user)
        device_token = data['device_token']
        print('device_token = ' + device_token)
        device_type = data['device_type']
        print('device_type = ' + device_type)

        # create the device user mapping
        try:
            # the user can be either a teacher or a parent. Look into parent first
            p = Parent.objects.get(parent_mobile1=user)
            the_mobile = p.parent_mobile1
            user_name = p.parent_name
            response_dict['user_type'] = 'Parent'
        except Exception as e:
            print('Exception 100 from authentication views.py = %s (%s)' % (e.message, type(e)))
            print('the user is not a parent. Can be a teacher or admin')
            try:
                t = Teacher.objects.get(email=user)
                the_mobile = t.mobile
                user_name = t.first_name
                response_dict['user_type'] = 'Teacher/Admin'
            except Exception as e:
                print('Exception 110 from authentication views.py = %s (%s)' % (e.message, type(e)))
                print('no teacher or parent could be mapped to the user ' + user)
                action_performed = 'Could not create user device mapping for ' + user
                print (action_performed)
                response_dict['action_performed'] = action_performed
                response_dict['user_type'] = 'Undetermined'
                response_dict['status'] = 'failed'
                return JSONResponse(response_dict, status=201)
        try:
            u = User.objects.get(username=user)
            # create the fcm device
            # try:
            #     fcm_device, created = GCMDevice.objects.get_or_create(registration_id=device_token)
            #     if created:
            #         print('device created')
            #         fcm_device.name = user_name
            #         fcm_device.user = u
            #         fcm_device.save()
            #     else:
            #         print('device already existed')
            #     try:
            #         fcm_device.send_message('Welcome to ClassUp')
            #     except Exception as e:
            #         print('Exception 160 from authentication views.py %s (%s)' % (e.message , type(e)))
            #         print('failed to send welcome notification to ' + user_name)
            # except urllib2.HTTPError, err:
            #     print('Exception 150 from authentication views.py %s (%s)' % (err.message, type(err)))
            #     print err.code
            # except Exception as e:
            #     print('Exception 140 from authentication views.py %s (%s)' % (e.message, type(e)))
            #     print('device creation failed')

            # now, create the mapping
            mapping = user_device_mapping.objects.get(user=u)
            mapping.mobile_number = the_mobile
            mapping.token_id = device_token
            mapping.device_type = device_type
            mapping.save()
            response_dict['status'] = 'success'
            action_performed = 'Existing Mapping Updated for user ' + user
            print(action_performed)
            response_dict['action_performed'] = action_performed
            return JSONResponse(response_dict, status=200)
        except Exception as e:
            print('Exception 120 from authentication views.py = %s (%s)' % (e.message , type(e)))
            print('user device mapping does not exist for ' + user + '. Hence Creating')
            try:
                mapping = user_device_mapping(user=u)
                mapping.mobile_number = the_mobile
                mapping.token_id = device_token
                mapping.device_type = device_type
                mapping.save()
                action_performed = 'Created Mapping for user ' + user
                print(action_performed)
                response_dict['action_performed'] = action_performed
                response_dict['status'] = 'success'
                return JSONResponse(response_dict, status=200)
            except Exception as e:
                print('Exception 130 from authentication views.py = %s (%s)' % (e.message, type(e)))
                action_performed = 'Could not create mapping for user ' + user
                print (action_performed)
                response_dict['action_performed'] = action_performed
                response_dict['status'] = 'failed'
                return JSONResponse(response_dict, status=201)


@csrf_exempt
def change_password(request):
    return_data = {

    }
    if request.method == 'POST':
        print ('request body = ' + request.body)

        data = json.loads(request.body)
        print (data)
        user = data["user"]
        print (user)
        log_entry(user, "Password Change Initiated", "Normal", True)
        new_password = data["new_password"]
        print (new_password)

        try:
            u = User.objects.get(username=user)
            u.set_password(new_password)
            u.save()
            log_entry(user, "Password Change Successful", "Normal", True)
            return_data["password_change"] = "Successful"
            return JSONResponse(return_data, status=200)
        except Exception as e:
            log_entry(user, "Password Change Failed", "Normal", False)
            print('unable to change password for ' + user)
            print('Exception 11 from authentication views.py = %s (%s)' % (e.message, type(e)))
            return_data["password_change"] = "Fail"
            return JSONResponse(return_data, status=400)

    return HttpResponse('OK', status=200)


@csrf_exempt
def forgot_password(request):
    return_data = {

    }
    if request.method == 'POST':
        print ('request body = ' + request.body)

        data = json.loads(request.body)
        print (data)
        user = data["user"]
        print (user)

        try:
            u = User.objects.get(username=user)

            # 04/03/17 - admin users should not be allowed to reset password from device. They should contact us
            if u.first_name == 'admin' or u.first_name == 'Admin':
                log_entry(user, "Forgot Password", "Normal", False)
                return_data["forgot_password"] = "fail"
                error_message = 'For password reset of Admin user, please contact ClassUp Support'
                print(error_message)
                return_data['error_message'] = error_message
                return JSONResponse(return_data, status=201)
            else:
                # 10/02/17 - users sometimes (well, most times) press the forgot password button repeatedly several times.
                # This causes multiple password generation and sms sending. User receives multiple password so, gets
                # confused and multiple sms are sent which impacts our profitability. Hence we will not reset pssword,
                # if it has been reset in last 15 minutes
                try:
                    lpt = LastPasswordReset.objects.get(login_id=user)
                    last_reset_time = lpt.last_reset_time
                    current_time = datetime.datetime.now()
                    time_difference = current_time - last_reset_time
                    print('time_difference = ' + str(time_difference))
                    if time_difference > datetime.timedelta(minutes=15):
                        print('time difference between last password reset and current attempt is more than 15 min.')
                        should_reset = True
                        lpt.last_reset_time = datetime.datetime.now()

                        try:
                            lpt.save()
                        except Exception as e:
                            log_entry(user,
                                      "Password Change exception (authentication view.py Exception 22", "Normal", False)
                            print('unable to reset the last password reset time for user ' + user)
                            print('Exception 22 from authentication views.py %s (%s)' % (e.message, type(e)))
                    else:
                        log_entry(user, "Password Change in less than 15 minutes", "Normal", False)
                        print('the user ' + user +
                              ' tried to reset password less than 15 min ago. Hence not resetting now')
                        should_reset = False
                        return_data["forgot_password"] = "successful"
                except Exception as e:
                    # this user is resetting the password for the first time
                    should_reset = True
                    print(user + ' is changing password for the first time')
                    print('Exception 20 from authentication views.py = %s (%s)' % (e.message, type(e)))
                    log_entry(user,
                              "Password Change exception (authentication view.py Exception 20", "Normal", True)

                    # create an entry for this user in the LastPasswordReset table
                    try:
                        lpt = LastPasswordReset(login_id=user, last_reset_time=datetime.datetime.now())
                        lpt.save()
                    except Exception as e:
                        print('unable to create an entry in the LastPasswordReset table for user ' + user)
                        print('Exception 21 from authentication views.py %s (%s)' % (e.message, type(e)))
                        log_entry(user,
                                  "Password Change exception (authentication view.py Exception 21", "Normal", False)

                if should_reset:
                    new_password = User.objects.make_random_password(length=5, allowed_chars='1234567890')
                    print (new_password)
                    log_entry(user, "New Password Generated", "Normal", True)
                    u.set_password(new_password)
                    u.save()
                    message_type = 'Forgot Password'
                    message = 'Dear ' + u.first_name + ' ' + u.last_name + ', your new password is ' + new_password
                    message += '. Regards, ClassUp Support'
                    print(message)
                    log_entry(user, "Forgot password SMS created", "Normal", True)

                    # check if user is teacher or parent
                    if u.is_staff:
                        # a teacher's user is created as his/her email id
                        teacher = Teacher.objects.get(email=u.email)
                        mobile = teacher.mobile
                        school = teacher.school
                    else:
                        # a parent's mobile is their username
                        mobile = user
                        # we need to extract the school name this parent belong to. First get the parent
                        p = Parent.objects.get(Q(parent_mobile1=mobile) | Q(parent_mobile2=mobile))
                        # now get the children of this parent
                        ward_list = Student.objects.filter(parent=p, active_status=True)
                        # finally, get the school
                        for student in ward_list:
                            school = student.school
                    log_entry(user, "New Password SMS sending initiated", "Normal", True)
                    sms.send_sms1(school, user, mobile, message, message_type)
                    log_entry(user, "New Password SMS Sending completed", "Normal", True)

                    return_data["forgot_password"] = "successful"
                    log_entry(user, "Forgot Password process completed", "Normal", True)
                    return JSONResponse(return_data, status=200)
        except Exception as e:
            print('unable to reset password for ' + user)
            print('Exception 6 from authentication views.py = %s (%s)' % (e.message, type(e)))
            log_entry(user, "Forgot Password process failed authentication view.py Exception 6", "Normal", True)
            return_data["forgot_password"] = "Fail"
            error_message = 'User does not exist'
            print(error_message)
            return_data['error_message'] = error_message
            return JSONResponse(return_data, status=201)

    return JSONResponse(return_data, status=200)


def logout_view(request):
    try:
        del request.session['school_id']
    except KeyError:
        pass
    logout(request)


def check_subscription(request, student_id):
    return_data = {

    }
    if request.method == 'GET':
        try:
            student = Student.objects.get(id=student_id)
            school = student.school
            if school.subscription_active:
                return_data['subscription'] = 'active'
            else:
                return_data['subscription'] = 'expired'
                error_message = 'Subscription of ' + school.school_name + ' has expired. '
                error_message += 'Please request the school/institute to renew the subscription with ClassUp.'
                return_data['error_message'] = error_message
            return JSONResponse(return_data, status=200)
        except Exception as e:
            print('unable to retrieve subscription status for  ' + school.school_name)
            print('Exception 7 from authentication views.py = %s (%s)' % (e.message, type(e)))
            return JSONResponse(return_data, status=400)
    return JSONResponse(return_data, status=200)
