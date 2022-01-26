import datetime
import os

from django.contrib.auth import login, logout
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.transaction import atomic
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from knox.views import LoginView as KnoxLoginView
from knox.views import LogoutView as KnoxLogoutView
# Create your views here.
from rest_framework import permissions, status
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from library.models import Book, Student, User, Borrower
from library.permissions import MasterDataPermission
from library.serializer import UserSerializer, BookSerializer, StudentSerializer, BorrowerSerializer
from libraryMgntSystem import settings

'''Admin can be added and by default the permission would be admin'''
class AdminRegistrationView(APIView):
    permission_classes = [
        AllowAny,
    ]

    @atomic
    def post(self, request, *args, **kwargs):
        mobile_no = self.request.data["mobile_no"]
        email = self.request.data["email"]
        password = self.request.data["password"]
        first_name = self.request.data.get("first_name")
        last_name = self.request.data.get("last_name")
        if User.objects.filter(email=email).exists():
            return JsonResponse(
                data={"message": "Email already exist"},
            )
        elif User.objects.filter(mobile_no=mobile_no).exists():
            return JsonResponse(
                data={"message": "Mobile number already exist"},
            )
        else:
            user = User.objects.create_superuser(mobile_no, email, password)
            user.first_name = first_name or ""
            user.last_name = last_name or ""
            user.save()
            if user:
                user.groups.add(Group.objects.get(name="admin"))

            serializer = UserSerializer(user)
            result = {
                "user": serializer.data,
                "roles": "admin",
            }
            return JsonResponse(data=result, safe=False)



class LoginResponseViewMixin:
    def get_post_response_data(self, request, token, instance):
        print("INSIDE LoginResponseViewMixin")

        serializer = self.response_serializer_class(
            data={
                "expiry": self.format_expiry_datetime(instance.expiry),
                "token": token,
                "user": self.get_user_serializer_class()(
                    request.user, context=self.get_context()
                ).data,
            }
        )
        # Note: This serializer was only created to easily document on swagger
        # the return of this endpoint, so the validation it's not really used
        serializer.is_valid(raise_exception=True)
        print("DONE")
        return serializer.initial_data


class LoginView(KnoxLoginView, LoginResponseViewMixin):
    """
    Login view adapted for our needs. Since by default all user operations
    need to be authenticated, we need to explicitly set it to AllowAny.
    """

    permission_classes = [
        AllowAny,
    ]

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        data = request.data
        if not User.objects.filter(email__exact=data["email"]).exists():
            return Response(
                data={"message": "Invalid Email"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = User.objects.get(email__exact=data["email"])
        password = data["password"]
        if not check_password(password, user.password):
            return Response(
                data={"message": "Invalid Password."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        groups = user.groups.all().values_list("name", flat=True)
        if (
                not getattr(user, "is_active", None)
        ):
            raise AuthenticationFailed(
                "User mobile is not verified.", code="account_disabled"
            )
        res = login(request, user)

        result = super(LoginView, self).post(request, format=None)
        serializer = UserSerializer(user)
        result.data["user"] = serializer.data
        result.data["roles"] = groups[0]
        return Response(result.data)


class LogoutView(KnoxLogoutView):
    @csrf_exempt
    def post(self, request, *args, **kwargs):
        request._auth.delete()
        logout(request)
        return Response(
            data={"message": "Logged out successfully"},
        )


class PublicBookView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, *args, **kwargs):
        book = Book.objects.filter(is_deleted=False,available_copies__gt=1).order_by('-available_copies')
        serializer = BookSerializer(book, many=True)
        return Response(serializer.data)


class BookView(APIView):
    permission_classes = [MasterDataPermission]


    def get(self, request, *args, **kwargs):
        try:
            book_id = self.kwargs["id"]
            if Book.objects.filter(
                    book_id=book_id, is_deleted=False
            ).exists():
                book = Book.objects.get(
                    book_id=book_id, is_deleted=False
                )
                serializer = BookSerializer(book)
                return Response(serializer.data)
            else:
                return Response(
                    data={"message": "Details Not Found."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        except:
            book = Book.objects.filter(is_deleted=False).order_by('-available_copies')
            serializer = BookSerializer(book, many=True)
            return Response(serializer.data)


    def delete(self, request, *args, **kwargs):
        try:
            id = self.kwargs["id"]
            book = Book.objects.get(book_id=id)
            book.is_deleted = True
            book.save()
            return Response(
                data={"message": "Book Deleted Successfully(Soft Delete)."},
            )
        except:
            return Response(
                data={"message": "Book Not Found."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

    def post(self, request, *args, **kwargs):
        data = self.request.data
        user = request.user
        serializer = BookSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save(validated_data=data)
        book = Book.objects.get(book_id=result)
        serializer = BookSerializer(book)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        data = self.request.data
        id = self.kwargs["id"]
        book = Book.objects.get(book_id=id, is_deleted=False)
        serializer = BookSerializer(book, data=data)
        serializer.is_valid(raise_exception=True)
        result = serializer.update(instance=book, validated_data=data)
        if result:
            book = Book.objects.get(book_id=result)
            serializer = BookSerializer(book)
            return Response(serializer.data)
        else:
            return Response(
                data={
                    "message": "Book Not Found"
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )


class StudentView(APIView):
    permission_classes = [MasterDataPermission]

    def get(self, request, *args, **kwargs):
        try:
            student_uuid = self.kwargs["id"]
            if Student.objects.filter(
                    user__user_id=student_uuid, is_deleted=False
            ).exists():
                book = Student.objects.get(
                    user__user_id=student_uuid, is_deleted=False
                )
                serializer = StudentSerializer(book)
                return Response(serializer.data)
            else:
                return Response(
                    data={"message": "Details Not Found."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        except:
            book = Student.objects.filter(is_deleted=False).order_by('user__first_name')
            serializer = StudentSerializer(book, many=True)
            return Response(serializer.data)

    @atomic
    def post(self, request, *args, **kwargs):
        data = self.request.data
        serializer = StudentSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        if Student.objects.filter(
                email=data["email"]).exists() or User.objects.filter(
            email=data["email"]).exists():
            return Response(
                data={
                    "message": "Email already Exists."
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        else:
            password = User.objects.make_random_password()
            result = serializer.save(validated_data=data, password=password)
            stu = Student.objects.get(user__user_id=result)
            user = User.objects.filter(email__exact=stu.user.email).first()
            if user:
                user.groups.add(Group.objects.get(name="student"))
            serializer = StudentSerializer(stu)
            return JsonResponse(serializer.data, safe=False)


class BorrowerView(APIView):
    permission_classes = (MasterDataPermission,)

    def get(self, request, *args, **kwargs):
        try:
            borrower_id = self.kwargs["id"]
            if Borrower.objects.filter(
                    borrower_id=borrower_id, is_deleted=False
            ).exists():
                book = Borrower.objects.get(
                    borrower_id=borrower_id, is_deleted=False
                )
                serializer = BorrowerSerializer(book)
                return Response(serializer.data)
            else:
                return Response(
                    data={"message": "Details Not Found."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        except:
            book = Borrower.objects.filter(is_deleted=False)
            serializer = BorrowerSerializer(book, many=True)
            return Response(serializer.data)

    @atomic
    def post(self, request, *args, **kwargs):
        data = self.request.data
        serializer = StudentSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        if Student.objects.filter(
                email=data["email"]).exists() or User.objects.filter(
            email=data["email"]).exists():
            return Response(
                data={
                    "message": "Email already Exists."
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        else:
            password = User.objects.make_random_password()
            result = serializer.save(validated_data=data, password=password)
            stu = Student.objects.get(user__user_id=result)
            serializer = StudentSerializer(stu)
            return JsonResponse(serializer.data, safe=False)


class FileUpload(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        if "file" not in request.data:
            return Response(
                data={"message": "No file Found"},
            )

        file = request.data["file"]
        doc_type = self.request.GET["doc_type"]
        filename, extension = os.path.splitext(file.name)
        timestamp = int(datetime.datetime.now().timestamp())
        filename = f"{filename}_{timestamp}{extension}"
        if doc_type == "profile_photo":
            student_id = self.request.GET["student_id"]
            doc = Student.objects.get(user__user_id=student_id, is_deleted=False)
            allowed_extensions = ["jpg", "jpeg", "png"]
            if extension.lower() in allowed_extensions:
                path = f"student_data/{doc.user.user_id}/profile_photo.{extension.lower()}"
                default_storage.save(
                    f"{settings.MEDIA_ROOT}/{path}",
                    ContentFile(file.read()),
                )
                temp_path = f"{settings.BASE_URL}{settings.MEDIA_URL}{path}"
                doc.profile = temp_path
                doc.save()
            else:
                return Response(
                    data={"message": "Enter file of type jpg,jpeg and png."},
                )

        elif doc_type == "book":
            book_id = self.request.GET["book_id"]
            doc = Book.objects.get(book_id=book_id,is_deleted=False)
            path = f"book_photo/{doc.book_id}/{filename}"
            default_storage.save(
                f"{settings.MEDIA_ROOT}/{path}",
                ContentFile(file.read()),
            )
            temp_path = f"{settings.BASE_URL}{settings.MEDIA_URL}{path}"
            doc.book_thumbnail = temp_path
            doc.save()
        return Response(
            data={
                "message": "File uploaded successfully",
                "photo": doc.book_thumbnail or doc.profile,
                "doc_id": doc.book_id or doc.user.user_id,
            }
        )
