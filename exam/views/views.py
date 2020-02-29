import ast

from django.shortcuts import render
from django.contrib import messages

from rest_framework.decorators import parser_classes
from rest_framework.parsers import MultiPartParser

from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework import generics

import xlrd

from setup.forms import ExcelFileUploadForm
from setup.models import School
from setup.views import validate_excel_extension

from student.models import Student
from academics.models import Class, Subject, ThirdLang, ClassTest, Exam, TermTestResult, TestResults

from exam.models import Scheme, HigherClassMapping, Stream, StreamMapping, Wing


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


@parser_classes((MultiPartParser,))
class UploadMarks(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request, format=None):
        print('resuest = ')
        print(request.FILES)
        context_dict = {

        }

        try:
            print ('now starting to process the uploaded file for marks upload...')
            fileToProcess_handle = request.FILES['computer_marks.xlsx']

            # check that the file uploaded should be a valid excel
            # file with .xls or .xlsx

            # if this is a valid excel file - start processing it
            fileToProcess = xlrd.open_workbook(filename=None, file_contents=fileToProcess_handle.read())
            sheet = fileToProcess.sheet_by_index(0)
            if sheet:
                print ('Successfully got hold of sheet!')
            for row in range(sheet.nrows):
                # first two rows are header rows
                if row == 0:
                    continue
                else:
                    erp_id = str(sheet.cell(row, 0).value)
                    school = School.objects.get(id=23)
                    try:
                        student = Student.objects.get(school=school, student_erp_id=erp_id)
                        print('now dealing with %s' % student)
                        theory = sheet.cell(row, 3).value
                        practical = sheet.cell(row, 4).value
                        subject = Subject.objects.get(school=school, subject_name='Computer Science')
                        exam = Exam.objects.get(school=school, title='Term-I (IX - X)')
                        class_test = ClassTest.objects.get(subject=subject, exam=exam,
                                                           the_class=student.current_class,
                                                           section=student.current_section)
                        test_result = TestResults.objects.get(student=student, class_test=class_test)
                        test_result.marks_obtained = float(theory)
                        test_result.save()
                        ttr = TermTestResult.objects.get(test_result=test_result)
                        ttr.prac_marks = float(practical)
                        ttr.save()
                    except Exception as e:
                        print('exception 02102019-A from exam views.py %s %s' % (e.message, type(e)))
        except Exception as e:
            print('exception 02102019-B from exam views.py %s %s' % (e.message, type(e)))
        return render(request, 'classup/setup_index.html', context_dict)


def setup_scheme(request):
    context_dict = {'user_type': 'school_admin', 'school_name': request.session['school_name']}

    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return render(request, 'classup/setup_index.html', context_dict)

    # now start processing the file upload

    context_dict['header'] = 'Setup Scheme'
    if request.method == 'POST':
        school_id = request.session['school_id']
        school = School.objects.get(id=school_id)

        # get the file uploaded by the user
        form = ExcelFileUploadForm(request.POST, request.FILES)
        context_dict['form'] = form

        if form.is_valid():
            try:
                print ('now starting to process the uploaded file for scheme setup...')
                fileToProcess_handle = request.FILES['excelFile']

                # check that the file uploaded should be a valid excel
                # file with .xls or .xlsx
                if not validate_excel_extension(fileToProcess_handle, form, context_dict):
                    return render(request, 'classup/setup_data.html', context_dict)

                # if this is a valid excel file - start processing it
                fileToProcess = xlrd.open_workbook(filename=None, file_contents=fileToProcess_handle.read())
                sheet = fileToProcess.sheet_by_index(0)
                if sheet:
                    print ('Successfully got hold of sheet!')
                for row in range(sheet.nrows):
                    if row == 0:
                        continue
                    print ('Processing a new row')
                    standard = sheet.cell(row, 0).value
                    print(standard)
                    try:
                        the_class = Class.objects.get(school=school, standard=standard)
                        print ('now dealing with class %s of %s' % (standard, school.school_name))
                    except Exception as e:
                        print ('exception 011117-A from exam views.py %s %s ' % (e.message, type(e)))
                        continue

                    for col in range(1, 11):
                        sub = sheet.cell(row, col).value
                        print(sub)
                        if sub == 'N/A':
                            continue

                        try:
                            subject = Subject.objects.get(school=school, subject_name=sub)
                        except Exception as e:
                            print ('exception 011117-B from exam views.py %s %s ' % (e.message, type(e)))
                            continue

                        sequence = col
                        try:
                            scheme = Scheme.objects.get(school=school, the_class=the_class, subject=subject)
                            print('subject %s in the scheme of class %s of school %s already exist. '
                                  'This will be updated' % (sub, standard, school.school_name))
                            scheme.sequence = sequence
                            scheme.subject = subject
                            try:
                                scheme.save()
                                print ('successfully updated the scheme of subject %s of class %s of school %s' %
                                       (sub, standard, school.school_name))
                            except Exception as e:
                                print ('failed to updated the scheme of subject %s of class %s of school %s' %
                                       (sub, standard, school.school_name))
                                print('exception 021117-B exam views.py %s %s ' % (e.message, type(e)))
                        except Exception as e:
                            print('scheme of subject %s of class %s of school %s is not set yet. This will be created' %
                                  (sub, standard, school.school_name))
                            print('exception 201117-C from exam views.py %s %s' % (e.message, type(e)))
                            try:
                                scheme = Scheme(school=school, the_class=the_class, sequence=sequence, subject=subject)
                                scheme.save()
                                print ('successfully created the scheme of subject %s of class %s of school %s' %
                                       (sub, standard, school.school_name))
                            except Exception as e:
                                print ('failed in creating the scheme of subject %s of class %s of school %s' %
                                       (sub, standard, school.school_name))
                                print ('exception 021117-D from exam views.py %s %s' % (e.message, type(e)))

                # file upload and saving to db was successful. Hence go back to the main menu
                messages.success(request, 'Scheme successfully uploaded')
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                error = 'invalid excel file uploaded.'
                print (error)
                print ('exception 021117-E from exam views.py %s %s ' % (e.message, type(e)))
                form.errors['__all__'] = form.error_class([error])
                return render(request, 'classup/setup_data.html', context_dict)
    else:
        form = ExcelFileUploadForm()
        context_dict['form'] = form
    return render(request, 'classup/setup_data.html', context_dict)


def setup_higher_class_subject_mapping(request):
    context_dict = {'user_type': 'school_admin', 'school_name': request.session['school_name']}

    maths_stream = ['English', 'Mathematics', 'Physics', 'Chemistry']
    biology_stream = ['English', 'Biology', 'Physics', 'Chemistry']
    commerce_stream = ['English', 'Economics', 'Accountancy', 'Business Studies']
    humanities_stream = ['English', 'Socialogy', 'History', 'Economics']
    maths = 'Mathematics'
    bio = 'Biology'
    commerce = 'Commerce'
    humanities = 'Humanities'

    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return render(request, 'classup/setup_index.html', context_dict)

    context_dict['header'] = 'Subject Mapping for Higher Classes'
    if request.method == 'POST':
        school_id = request.session['school_id']
        school = School.objects.get(id=school_id)
        print (school)

        # get the file uploaded by the user
        form = ExcelFileUploadForm(request.POST, request.FILES)
        context_dict['form'] = form

        if form.is_valid():
            try:
                print ('now starting to process the uploaded file for Higher classes subject mapping...')
                fileToProcess_handle = request.FILES['excelFile']
                # check that the file uploaded should be a valid excel
                # file with .xls or .xlsx
                if not validate_excel_extension(fileToProcess_handle, form, context_dict):
                    return render(request, 'classup/setup_data.html', context_dict)

                # if this is a valid excel file - start processing it
                fileToProcess = xlrd.open_workbook(filename=None, file_contents=fileToProcess_handle.read())
                sheet = fileToProcess.sheet_by_index(0)
                if sheet:
                    print ('Successfully got hold of sheet! the chako')
                for row in range(sheet.nrows):
                    # get the subject name
                    if row != 0:
                        erp = str(sheet.cell(row, 1).value)
                        print(erp)
                        try:
                            student = Student.objects.get(school=school, student_erp_id=erp)
                            student_name = '%s %s' % (student.fist_name, student.last_name)

                            stream = (sheet.cell(row, 5).value).title()

                            print('stream chosen by %s is %s' % (student_name, stream))
                            if stream == maths:
                                print('going to set the chosen_stream to be %s' % stream)
                                chosen_stream = list(maths_stream)
                                print('chosen_stream = Mathematics')
                                try:
                                    m_stream = Stream.objects.get(stream='Mathematics')
                                    stream_mapping = StreamMapping.objects.get_or_create(student=student,
                                                                                         stream=m_stream)
                                    print('set Mathematics for %s' % student)
                                    print(stream_mapping)
                                except Exception as e:
                                    print('failed to create %s stream mapping for %s' % (stream, student))
                                    print('exception 08062019-A from exam views.py %s %s' % (e.message, type(e)))

                            if stream == bio:
                                print('going to set the chosen_stream to be %s' % stream)
                                chosen_stream = list(biology_stream)
                                print('chosen_stream = Biology')
                                try:
                                    b_stream = Stream.objects.get(stream='Biology')
                                    stream_mapping = StreamMapping.objects.get_or_create(student=student,
                                                                                         stream=b_stream)
                                    print('set biology for %s' % student)
                                    print(stream_mapping)
                                except Exception as e:
                                    print('failed to create %s stream mapping for %s' % (stream, student))
                                    print('exception 08062019-B from exam views.py %s %s' % (e.message, type(e)))

                            if stream == commerce:
                                print('going to set the chosen_stream to be %s' % stream)
                                chosen_stream = list(commerce_stream)
                                print('chosen_stream = Commerce')
                                try:
                                    c_stream = Stream.objects.get(stream='Commerce')
                                    stream_mapping = StreamMapping.objects.get_or_create(student=student,
                                                                                         stream=c_stream)
                                    print('set Commerce for %s' % student)
                                    print(stream_mapping)
                                except Exception as e:
                                    print('failed to create %s stream mapping for %s' % (stream, student))
                                    print('exception 08062019-C from exam views.py %s %s' % (e.message, type(e)))

                            if stream == humanities:
                                print('going to set the chosen_stream to be %s' % stream)
                                chosen_stream = list(humanities_stream)
                                print('chosen_stream = Humanities')
                                try:
                                    h_stream = Stream.objects.get(stream='Humanities')
                                    stream_mapping = StreamMapping.objects.get_or_create(student=student,
                                                                                         stream=h_stream)
                                    print('set Humanities for %s' % student)
                                    print(stream_mapping)
                                except Exception as e:
                                    print('failed to create %s stream mapping for %s' % (stream, student))
                                    print('exception 08062019-D from exam views.py %s %s' % (e.message, type(e)))

                            elective = (sheet.cell(row, 6).value).title()
                            print('elective chosen by %s is %s' % (student_name, elective))

                            try:
                                chosen_stream.append(str(elective))
                                print('complete list of subjects to be mapped for %s' % student_name)
                                print(chosen_stream)
                            except Exception as e:
                                print('failed to add elective %s to chosen stream' % elective)
                                print('exception 28122018-A from exam views.py %s %s' % (e.message, type(e)))

                            print('setting stream %s  & elective %s for %s' % (stream, elective, student_name))
                            for sub in chosen_stream:
                                try:
                                    subject = Subject.objects.get(school=school, subject_name=sub)
                                    print('retrieved the subject object for %s' % sub)
                                    mapping = HigherClassMapping.objects.get(student=student, subject=subject)
                                    print ('subject %s mapping for %s already exist. Not doing again.' % (
                                        sub, student_name))
                                except Exception as e:
                                    print ('exception 141117-C from exam views.py %s %s' % (e.message, type(e)))
                                    print ('subject %s mapping for %s does not exist. Hence creating...' % (
                                        sub, student_name))
                                    try:
                                        mapping = HigherClassMapping(student=student, subject=subject)
                                        mapping.save()
                                        print ('created %s subject mapping for % s' % (sub, student_name))
                                    except Exception as e:
                                        print ('exception 141117-D from exam views.py %s %s' % (e.message, type(e)))
                                        print ('failed to create %s subject mapping for %s' % (sub, student_name))
                        except Exception as e:
                            print ('failed to create subject mapping')
                            print ('exception 141117-A from exam views.py %s %s' % (e.message, type(e)))
            except Exception as e:
                error = 'invalid excel file uploaded.'
                print (error)
                print ('exception 141117-B from exam views.py %s %s' % (e.message, type(e)))
                form.errors['__all__'] = form.error_class([error])
                return render(request, 'classup/setup_data.html', context_dict)
    else:
        form = ExcelFileUploadForm()
        context_dict['form'] = form
    return render(request, 'classup/setup_data.html', context_dict)


def setup_third_lang(request):
    context_dict = {
    }
    context_dict['user_type'] = 'school_admin'
    context_dict['school_name'] = request.session['school_name']

    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return render(request, 'classup/setup_index.html', context_dict)

    # now start processing the file upload

    context_dict['header'] = 'Setup Third Language'
    if request.method == 'POST':
        school_id = request.session['school_id']
        school = School.objects.get(id=school_id)

        # get the file uploaded by the user
        form = ExcelFileUploadForm(request.POST, request.FILES)
        context_dict['form'] = form

        if form.is_valid():
            try:
                print ('now starting to process the uploaded file for Third Language mapping...')
                fileToProcess_handle = request.FILES['excelFile']

                # check that the file uploaded should be a valid excel
                # file with .xls or .xlsx
                if not validate_excel_extension(fileToProcess_handle, form, context_dict):
                    return render(request, 'classup/setup_data.html', context_dict)

                # if this is a valid excel file - start processing it
                fileToProcess = xlrd.open_workbook(filename=None, file_contents=fileToProcess_handle.read())
                sheet = fileToProcess.sheet_by_index(0)
                if sheet:
                    print ('Successfully got hold of sheet!')
                for row in range(sheet.nrows):
                    if row == 0:
                        continue
                    print ('Processing a new row')
                    erp_id = sheet.cell(row, 1).value
                    print(erp_id)
                    try:
                        student = Student.objects.get(school=school, student_erp_id=erp_id)
                        print ('now dealing with %s %s' % (student.fist_name, student.last_name))
                    except Exception as e:
                        print ('student with erp id %s does not exist' % erp_id)
                        print ('exception 231017-G from exam views.py %s %s ' % (e.message, type(e)))
                        continue

                    # 31/10/2017 - get the third language
                    t_l = sheet.cell(row, 5).value
                    print('third language specified for %s %s in the sheet is %s' %
                          (student.fist_name, student.last_name, t_l))
                    try:
                        third_lang = Subject.objects.get(school=school, subject_name=t_l)
                    except Exception as e:
                        print('Exception 311017-A from exam views.py %s %s' % (e.message, type(e)))
                        print('%s is not a third languate!' % t_l)

                    try:
                        record = ThirdLang.objects.get(student=student)
                        print('third language for %s %s is already set as %s. This will be updated' %
                              (student.fist_name, student.last_name, record.third_lang.subject_name))
                        print ('third language ' + student.fist_name + ' ' +
                               student.last_name + ' already exists. This will be updated')
                        try:
                            record.third_lang = third_lang
                            record.save()
                            print('successfully updated third language for %s %s as %s' %
                                  (student.fist_name, student.last_name, t_l))
                            print ('successfully updated the third language for ' +
                                   student.fist_name, ' ' + student.last_name)
                        except Exception as e:
                            print ('failed to update the third language for ' +
                                   student.fist_name, ' ' + student.last_name)
                            print ('(exception 311017-B from exam views.py %s %s) ' % (e.message, type(e)))
                    except Exception as e:
                        print ('(exception 311017-C from exam views.py %s %s) ' % (e.message, type(e)))
                        print ('third language for ' + student.fist_name + ' ' +
                               student.last_name + ' is not in record. This will be created')
                        try:
                            new_record = ThirdLang(student=student, third_lang=third_lang)
                            new_record.save()
                            print (('created third language entry for %s %s)' %
                                    (student.fist_name, student.last_name)))
                        except Exception as e:
                            print ('failed to create third language entry for %s %s)' %
                                   (student.fist_name, student.last_name))
                            print ('(exception 311017-D from exam views.py %s %s) ' % (e.message, type(e)))

                            # file upload and saving to db was successful. Hence go back to the main menu
                messages.success(request, 'Third Language uploaded')
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                error = 'invalid excel file uploaded.'
                print (error)
                print ('exception 311017-E from exam views.py %s %s ' % (e.message, type(e)))
                form.errors['__all__'] = form.error_class([error])
                return render(request, 'classup/setup_data.html', context_dict)
    else:
        form = ExcelFileUploadForm()
        context_dict['form'] = form
    return render(request, 'classup/setup_data.html', context_dict)


def get_grade(marks):
    if 100 >= marks > 90:
        grade = 'A1'
        return grade
    if 90 >= marks > 80:
        grade = 'A2'
        return grade
    if 80 >= marks > 70:
        grade = 'B1'
        return grade
    if 70 >= marks > 60:
        grade = 'B2'
        return grade
    if 60 >= marks > 50:
        grade = 'C1'
        return grade
    if 50 >= marks > 40:
        grade = 'C2'
        return grade
    if 40 >= marks > 32:
        grade = 'D'
        return grade
    if marks <= 32:
        grade = 'E'
        return grade


def get_wings(school):
    wings = {

    }
    try:
        jc = Wing.objects.get(school=school, wing='junior_classes')
        junior_classes = ast.literal_eval(jc.classes)
        print('junior_classes for %s are: ' % school)
        print(junior_classes)
    except Exception as e:
        print('exception 26092019-A from exam views.py %s %s' % (e.message, type(e)))
        print('junior_classes not defined for %s' % school)
        junior_classes = ['not defined']
    wings['junior_classes'] = junior_classes

    try:
        mc = Wing.objects.get(school=school, wing='middle_classes')
        print('raw middle_classes retrieved for %s: %s. Will be converted to proper string now' %
              (school, mc.classes))
        middle_classes = ast.literal_eval(mc.classes)
        print('middle_classes for %s are: ' % school)
        print(middle_classes)
    except Exception as e:
        print('exception 26092019-B from exam views.py %s %s' % (e.message, type(e)))
        print('middle_classes not defined for %s' % school)
        middle_classes = ['not defined']
    wings['middle_classes'] = middle_classes

    try:
        nt = Wing.objects.get(school=school, wing='ninth_tenth')
        ninth_tenth = ast.literal_eval(nt.classes)
        print('ninth_tenth for %s are: ' % school)
        print(ninth_tenth)
    except Exception as e:
        print('exception 26092019-C from exam views.py %s %s' % (e.message, type(e)))
        print('ninth_tenth not defined for %s' % school)
        ninth_tenth = ['not defined']
    wings['ninth_tenth'] = ninth_tenth

    try:
        hc = Wing.objects.get(school=school, wing='higher_classes')
        higher_classes = ast.literal_eval(hc.classes)
        print('higher_classes for %s are: ' % school)
        print(higher_classes)
    except Exception as e:
        print('exception 26092019-D from exam views.py %s %s' % (e.message, type(e)))
        print('higher_classes not defined for %s' % school)
        higher_classes = ['not defined']
    wings['higher_classes'] = higher_classes

    return wings
