import json

from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt

from rest_framework.renderers import JSONRenderer


from .forms import ClassUpLoginForm

# Create your views here.

print 'in view.py for authentication'


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
                if user.groups.filter(name='school_admin').exists():
                    context_dict['user_type'] = 'school_admin'
                print context_dict
                return render(request, 'classup/setup_index.html', context_dict)
                #return HttpResponseRedirect(reverse('setup_index'), context_dict)
            else:
                error = 'User: '+ user_name +' is disabled. Please contact your administrator'
                login_form.errors['__all__'] = login_form.error_class([error])
                print error
                return render(request, 'classup/auth_login.html', context_dict)
        else:
            error = 'Invalid username/password. Please try again.'
            login_form.errors['__all__'] = login_form.error_class([error])
            print error
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
        print 'from JSONResponse...'
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


def auth_login_from_device(request, user_name, password):
    print 'Inside login from device view!'
    return_data = {

    }
    user = authenticate(username=user_name, password=password)
    if user is not None:
        if user.is_active:
            login(request, user)
            return_data["login"] = "successful"
            return_data["user_status"] = "active"
            return_data['user_name'] = user.first_name + ' ' + user.last_name

            if user.is_staff:
                return_data['is_staff'] = "true"
            else:
                return_data['is_staff'] = "false"
            return JSONResponse(return_data, status=200)
        else:
            return_data["login"] = "successful"
            return_data["user_status"] = "inactive"
            print return_data
            return JSONResponse(return_data, status=403)
    else:
        return_data["login"] = "failed"
        print return_data
        return JSONResponse(return_data, status=404)


@csrf_exempt
def auth_login_from_device1(request):
    print 'Inside login from device view!'
    return_data = {

    }
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
                else:
                    return_data['is_staff'] = "false"
                return JSONResponse(return_data, status=200)
            else:
                return_data["login"] = "successful"
                return_data["user_status"] = "inactive"
                print return_data
                return JSONResponse(return_data, status=403)
        else:
            return_data["login"] = "failed"
            print return_data
            return JSONResponse(return_data, status=404)


@csrf_exempt
def change_password(request):
    return_data = {

    }
    if request.method == 'POST':
        print 'request body = ' + request.body

        data = json.loads(request.body)
        print data
        user = data["user"]
        print user
        new_password = data["new_password"]
        print new_password

        try:
            u = User.objects.get(username=user)
            u.set_password(new_password)
            u.save()
            return_data["password_change"] = "Successful"
            return JSONResponse(return_data, status=200)
        except Exception as e:
            print('unable to change password for ' + user)
            print 'Exception = %s (%s)' % (e.message, type(e))
            return_data["password_change"] = "Fail"
            return JSONResponse(return_data, status=400)

    return HttpResponse('OK', status=200)


def logout_view(request):
    logout(request)
