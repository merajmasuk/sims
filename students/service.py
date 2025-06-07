

from .models import Student
from .serializers import StudentSerializer


class StudentServiceMethodHandler:
    @staticmethod
    def create_student_info(request):
        email = request.data["email"]
        existing_student = Student.objects.filter(email=email)
        if existing_student:
            raise LookupError("A student with the same email already exists")
        
        student = Student.objects.create(
            first_name=request.data["first_name"],
            last_name=request.data["last_name"],
            email=email,
            phone_number=request.data["phone_number"],
            date_of_birth=request.data["date_of_birth"]
        )
        return StudentSerializer(student).data


    @staticmethod
    def update_student_info(request, id):
        student = Student.objects.get(id=id)
        if not student:
            raise LookupError("Student record not found")

        data = request.data
        student.first_name = data["first_name"]
        student.last_name = data["last_name"]
        student.email = data["email"]
        student.phone_number = data["phone_number"]
        student.date_of_birth = data["date_of_birth"]
        student.save()

        return StudentSerializer(student).data
    
    @staticmethod
    def delete_student_info(id):
        student = Student.objects.get(id=id)
        if not student:
            raise LookupError("Student record not found")
        
        student.is_deleted = True
        student.save()

        return True
    
        
