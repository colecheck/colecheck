from apps.school.models import School, EducationLevel, Grade, Course, Section
from apps.student.models import Student
from apps.teacher.models import Teacher
from apps.director.models import Principal
from apps.assistant.models import Auxiliar
from django.contrib.auth.models import User
from rest_framework import serializers
from apps.assistance.models import DetailGeneralAssistance, GeneralAssistance


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ('id', 'name', 'slug', 'slogan', 'logo')


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'


class GeneralAssistanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneralAssistance
        fields = '__all__'


class DetailGeneralAssistanceSerializer(serializers.ModelSerializer):
    student = StudentSerializer()

    class Meta:
        model = DetailGeneralAssistance
        fields = '__all__'


class EducationLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationLevel
        fields = '__all__'


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = '__all__'


class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = '__all__'


class TeacherSerializer(serializers.ModelSerializer):
    user_type = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()

    def get_username(self, obj):
        return obj.user.username if obj.user else None

    def get_first_name(self, obj):
        return obj.user.first_name if obj.user else None

    def get_last_name(self, obj):
        return obj.user.last_name if obj.user else None

    def get_user_type(self, obj):
        return "teacher"

    class Meta:
        model = Teacher
        fields = '__all__'


class AuxiliarSerializer(serializers.ModelSerializer):
    user_type = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()

    def get_username(self, obj):
        return obj.user.username if obj.user else None

    def get_first_name(self, obj):
        return obj.user.first_name if obj.user else None

    def get_last_name(self, obj):
        return obj.user.last_name if obj.user else None

    def get_user_type(self, obj):
        return "teacher"

    class Meta:
        model = Auxiliar
        fields = '__all__'


class PrincipalSerializer(serializers.ModelSerializer):
    user_type = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()

    def get_username(self, obj):
        return obj.user.username if obj.user else None

    def get_first_name(self, obj):
        return obj.user.first_name if obj.user else None

    def get_last_name(self, obj):
        return obj.user.last_name if obj.user else None

    def get_user_type(self, obj):
        return "director"

    class Meta:
        model = Principal
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'email']


class NumberSerializer(serializers.Serializer):
    number = serializers.FloatField()