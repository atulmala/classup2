from rest_framework import serializers

from .models import Bus_Rout, Student_Rout, Bus_Attendance, BusStop


class BusRoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bus_Rout
        fields = ('bus_root',)


class BusRoutStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student_Rout
        fields = ('student',)


class BusAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bus_Attendance
        fields = ('student', 'date', )


class BusStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusStop
