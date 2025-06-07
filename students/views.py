from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from rest_framework.views import APIView

import traceback

from utils.core.response import UtilsResponse
from .forms import StudentForm
from .models import Student
from .serializers import StudentSerializer
from . import service

# Create your views here.
@login_required
def index(request):
    return render(request, 'students/index.html', {
        'students': Student.objects.all()
    })


@login_required
def view_student(request, id):
    student = Student.objects.get(pk=id)
    return HttpResponseRedirect(reverse('index'))


@login_required
def add(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            new_student_number = form.cleaned_data['student_number']
            new_first_name = form.cleaned_data['first_name']
            new_last_name = form.cleaned_data['last_name']
            new_email = form.cleaned_data['email']
            new_field_of_study = form.cleaned_data['field_of_study']
            new_gpa = form.cleaned_data['gpa']

            new_student = Student(
                student_number = new_student_number,
                first_name = new_first_name,
                last_name = new_last_name,
                email = new_email,
                field_of_study = new_field_of_study,
                gpa = new_gpa
            )
            new_student.save()
            return render(request, 'students/add.html', {
                'form': StudentForm(),
                'success': True
            })
    else:
        form = StudentForm()
    return render(request, 'students/add.html', {
        'form': StudentForm()
    })


@login_required
def edit(request, id):
    if request.method == 'POST':
        student = Student.objects.get(pk=id)
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            return render(request, 'students/edit.html', {
                'form': form,
                'success': True
            })
    else:
        student = Student.objects.get(pk=id)
        form = StudentForm(instance=student)
    return render(request, 'students/edit.html', {
       'form': form
    })


@login_required
def delete(request, id):
    if request.method == 'POST':
        student = Student.objects.get(pk=id)
        student.delete()
    return HttpResponseRedirect(reverse('index'))


            

class StudentCreateAndListAPIViewSet(APIView):
    def get(self, request):
        try:
            students = Student.objects.all()
            response = StudentSerializer(students, many=True)
            return UtilsResponse.success(response)
        except Exception as e:
            print(traceback.format_exc())
            return UtilsResponse.request_error(str(e))
        
    def post(self, request):
        try:
            response = service.StudentServiceMethodHandler.create_student_info(request)
            return UtilsResponse.created()
        except Exception as e:
            print(traceback.format_exc())
            return UtilsResponse.request_error(str(e))        


class StudentAPIViewSet(APIView):
    def get(self, request, id):
        try:
            student = Student.objects.get(id=id)
            response = StudentSerializer(student).data
            return UtilsResponse.success(response)
        except Exception as e:
            print(traceback.format_exc())
            return UtilsResponse.request_error(str(e))

    def put(self, request, id):
        try:
            response = service.StudentServiceMethodHandler.update_student_info(request, id)
            return UtilsResponse.success(response)
        except Exception as e:
            print(traceback.format_exc())
            return UtilsResponse.request_error(str(e))

    def delete(self, request, id):
        try:
            service.StudentServiceMethodHandler.delete_student_info(id)
            return UtilsResponse.no_content()
        except Exception as e:
            print(traceback.format_exc())
            return UtilsResponse.request_error(str(e))
