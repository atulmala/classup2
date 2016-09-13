import json

from django.contrib.auth.models import User, Group
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt

from rest_framework.renderers import JSONRenderer

from setup.models import UserSchoolMapping
from teacher.models import Teacher
from student.models import Student
from operations import sms

from .forms import ClassUpLoginForm

# Create your views here.

print ('in view.py for authentication')


def auth_index(request):
    response = render(request, 'classup/auth_index.html')
    return response


def auth_login(request):
    context_dict = {
    }
    if request.method == 'POST':
        login_form = ClassUpLoginForm(request.POST)
        context_dict['form'] = login_form
        user_name = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=user_name, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                try:
                    u = UserSchoolMapping.objects.get(user=user)
                    school = u.school
                    request.session['school_name'] = school.school_name
                    context_dict['school_name'] = school.school_name
                    if school.subscription_active:
                        school_id = u.school.id
                        request.session['school_id'] = school_id
                        print ('school_id=' + str(school_id))
                    else:
                        error = school.school_name + "'s subscription has expired. "
                        error += 'Please contact ClassUp support at info@classup.in for renewal'
                        print(error)
                        login_form.errors['__all__'] = login_form.error_class([error])
                        return render(request, 'classup/auth_login.html', context_dict)
                except Exception as e:
                    print ('unable to retrieve schoo_id for ' + user.username)
                if user.groups.filter(name='school_admin').exists():
                    context_dict['user_type'] = 'school_admin'
                    request.session['user_type'] = 'school_admin'
                else:
                    context_dict['user_type'] = 'non_admin'
                    request.session['user_type'] = 'non_admin'
                print (context_dict)
                return render(request, 'classup/setup_index.html', context_dict)
            else:
                error = 'User: ' + user_name + ' is disabled. Please contact your administrator'
                login_form.errors['__all__'] = login_form.error_class([error])
                print (error)
                return render(request, 'classup/auth_login.html', context_dict)
        else:
            error = 'Invalid username/password or blank entry. Please try again.'
            login_form.errors['__all__'] = login_form.error_class([error])
            print (error)
            return render(request, 'classup/auth_login.html', context_dict)
    else:
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
    print ('Inside login from device view!')
    return_data = {

    }
    return_data['subscription'] = 'na'
    if request.method == 'POST':
        data = json.loads(request.body)
        the_user = data['user']
        password = data['password']
        user = authenticate(username=the_user, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return_data["login"] = "successful"
                return_data["user_status"] = "active"
                return_data['user_name'] = user.first_name + ' ' + user.last_name

                if user.is_staff:
                    return_data['is_staff'] = "true"
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
                        print ('unable to retrieve school_id for ' + user.username)
                else:
                    return_data['is_staff'] = "false"
                return JSONResponse(return_data, status=200)
            else:
                return_data["login"] = "successful"
                return_data['user_name'] = user.first_name + ' ' + user.last_name
                return_data["user_status"] = "inactive"
                print (return_data)
                return JSONResponse(return_data, status=200)
        else:
            return_data["login"] = "failed"
            print (return_data)
            return JSONResponse(return_data, status=200)


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
        new_password = data["new_password"]
        print (new_password)

        try:
            u = User.objects.get(username=user)
            u.set_password(new_password)
            u.save()
            return_data["password_change"] = "Successful"
            return JSONResponse(return_data, status=200)
        except Exception as e:
            print('unable to change password for ' + user)
            print('Exception = %s (%s)' % (e.message, type(e)))
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
            new_password = User.objects.make_random_password(length=5, allowed_chars='1234567890')
            print (new_password)
            u.set_password(new_password)
            u.save()
            message = 'Dear Ms/Mr ' + u.first_name + ' ' + u.last_name + ', your new password is ' + new_password
            message += '. Regards, ClassUp Support'
            print(message)

            # check if user is teacher or parent
            if u.is_staff:
                # a teacher's user is created as his/her email id
                teacher = Teacher.objects.get(email=u.email)
                mobile = teacher.mobile
            else:
                # a parent's mobile is their username
                mobile = user

            sms.send_sms(mobile, message)

            return_data["forgot_password"] = "successful"
            return JSONResponse(return_data, status=200)
        except Exception as e:
            print('unable to reset password for ' + user)
            print('Exception = %s (%s)' % (e.message, type(e)))
            return_data["forgot_password"] = "Fail"
            return JSONResponse(return_data, status=400)

    return HttpResponse('OK', status=200)


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
            print('Exception = %s (%s)' % (e.message, type(e)))
            return JSONResponse(return_data, status=400)
    return JSONResponse(return_data, status=200)
