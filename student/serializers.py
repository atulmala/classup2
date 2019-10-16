__author__ = 'atulgupta'


from rest_framework import serializers

from erp.models import CollectAdmFee
from .models import Student, Parent, AdditionalDetails, DOB, House
from bus_attendance.models import BusUser, Bus_Rout, BusStop, Student_Rout


class StudentSerializer(serializers.ModelSerializer):
    # we use SlugRelatedField because current_class and current_section are foreign keys in Student Model. Not using
    # slug related field would return the primary key instead of their respective names
    current_class = serializers.SlugRelatedField(read_only=True, slug_field='standard')
    current_section = serializers.SlugRelatedField(read_only=True, slug_field='section')
    parent = serializers.SlugRelatedField(read_only=True, slug_field='parent_name')
    parent_mob = serializers.SerializerMethodField()
    father_occ = serializers.SerializerMethodField()
    mother_occ = serializers.SerializerMethodField()
    mother = serializers.SerializerMethodField()
    mother_mob = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    dob = serializers.SerializerMethodField()
    gender = serializers.SerializerMethodField()
    blood_group = serializers.SerializerMethodField()
    adhar = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    bus_user = serializers.SerializerMethodField()
    bus_rout = serializers.SerializerMethodField()
    bus_stop = serializers.SerializerMethodField()
    house = serializers.SerializerMethodField()

    def get_bus_user(self, obj):
        try:
            bus_user = BusUser.objects.get(student=obj)
            print ('% is a bus user' % obj)
            return True
        except Exception as e:
            print('exception 12102019-A from student serializers.py %s %s' % (e.message, type(e)))
            print('%s is not a bus user' % obj)
            return False

    def get_bus_rout(self, obj):
        try:
            rout = Student_Rout.objects.get(student=obj)
            print ('%s is a bus user' % obj)
            return rout.bus_root.bus_root
        except Exception as e:
            # print('exception 12102019-B from student serializers.py %s %s' % (e.message, type(e)))
            # print('%s is not a bus user. Hence rout is N/A' % obj)
            return 'N/A'

    def get_bus_stop(self, obj):
        try:
            rout = Student_Rout.objects.get(student=obj)
            print ('%s is a bus user' % obj)
            return rout.bus_stop.stop_name
        except Exception as e:
            # print('exception 12102019-C from student serializers.py %s %s' % (e.message, type(e)))
            # print('%s is not a bus user. Hence bus stop is N/A' % obj)
            return 'N/A'

    def get_house(self, obj):
        try:
            house = House.objects.get(student=obj)
            return house.house
        except Exception as e:
            # print('exception 12102019-D from student serializers.py %s %s' % (e.message, type(e)))
            # print('no house assigned for %s' % obj)
            return 'Not Assigned'

    def get_mother(self, obj):
        try:
            ad = AdditionalDetails.objects.get(student=obj)
            return ad.mother_name
        except Exception as e:
            # print('exception 13102019-A from student serializers.py %s %s' % (e.message, type(e)))
            # print('addtional details (mother) not entered for %s' % obj)
            return 'Not Available'

    def get_mother_occ(self, obj):
        try:
            ad = AdditionalDetails.objects.get(student=obj)
            return ad.mother_occupation
        except Exception as e:
            # print('exception 13102019-H from student serializers.py %s %s' % (e.message, type(e)))
            # print('addtional details (mother occupation) not entered for %s' % obj)
            return 'Not Available'

    def get_father_occ(self, obj):
        try:
            ad = AdditionalDetails.objects.get(student=obj)
            return ad.father_occupation
        except Exception as e:
            # print('exception 13102019-I from student serializers.py %s %s' % (e.message, type(e)))
            # print('addtional details (father occupation) not entered for %s' % obj)
            return 'Not Available'

    def get_parent_mob(self, obj):
        return obj.parent.parent_mobile1

    def get_mother_mob(self, obj):
        return obj.parent.parent_mobile2

    def get_email(self, obj):
        return obj.parent.parent_email

    def get_dob(self, obj):
        try:
            dob = DOB.objects.get(student=obj)
            return dob.dob
        except Exception as e:
            # print('exception 13102019-B from student serializers.py %s %s' % (e.message, type(e)))
            # print('DOB not entered for %s' % obj)
            return 'Not Available'

    def get_gender(self, obj):
        try:
            ad = AdditionalDetails.objects.get(student=obj)
            return ad.gender
        except Exception as e:
            # print('exception 13102019-C from student serializers.py %s %s' % (e.message, type(e)))
            # print('addtional details (gender) not entered for %s' % obj)
            return 'Not Available'

    def get_blood_group(self, obj):
        try:
            ad = AdditionalDetails.objects.get(student=obj)
            return ad.blood_group
        except Exception as e:
            # print('exception 13102019-D from student serializers.py %s %s' % (e.message, type(e)))
            # print('addtional details (blood group) not entered for %s' % obj)
            return 'Not Available'

    def get_adhar(self, obj):
        try:
            ad = AdditionalDetails.objects.get(student=obj)
            return ad.adhar
        except Exception as e:
            # print('exception 13102019-E from student serializers.py %s %s' % (e.message, type(e)))
            # print('addtional details (adhar) not entered for %s' % obj)
            return 'Not Available'

    def get_address(self, obj):
        try:
            ad = AdditionalDetails.objects.get(student=obj)
            return ad.address
        except Exception as e:
            # print('exception 13102019-F from student serializers.py %s %s' % (e.message, type(e)))
            # print('addtional details (address) not entered for %s' % obj)
            return 'Not Available'

    class Meta:
        model = Student
        fields = ('id', 'student_erp_id', 'fist_name', 'last_name', 'roll_number', 'current_class',
                  'current_section', 'parent', 'parent_mob', 'mother', 'mother_mob', 'email', 'dob', 'gender',
                  'blood_group', 'adhar', 'address', 'bus_user', 'bus_rout', 'bus_stop', 'house',
                  'father_occ', 'mother_occ')


class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = ('parent_name', 'parent_mobile1', 'parent_mobile2',)

