import random

from rest_framework import serializers

from library.models import Book, Student, Borrower, User


class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(
        method_name="get_user_name", read_only=True
    )
    class Meta:
        model = User
        fields = (
            "user_id",
            "name",
            "username",
            "email",
            "mobile_no",
        )
    def get_user_name(self, obj):
        name = obj.get_full_name()
        return name

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = (
            "book_id",
            "author",
            "title",
            "available_copies",
            "total_copies",
            "summary",
            "book_thumbnail",
        )

    def save(self, validated_data):
        book = Book.objects.create(
            title=validated_data["title"],
            author=validated_data["author"],
            summary=validated_data["summary"],
            total_copies=validated_data["total_copies"],
            available_copies=validated_data["available_copies"],
            book_thumbnail=validated_data["book_thumbnail"],
        )
        return book.book_id

    def update(self, instance, validated_data):
        instance.title = validated_data.get("title")
        instance.author = validated_data.get("author")
        instance.summary = validated_data.get("summary")
        instance.total_copies = validated_data["total_copies"]
        instance.available_copies = validated_data["available_copies"]
        instance.book_thumbnail = validated_data["book_thumbnail"]
        instance.save()
        return instance.book_id


class StudentSerializer(serializers.ModelSerializer):
    student_id = serializers.UUIDField(source="user.user_id")
    user = serializers.SerializerMethodField(
        method_name="get_student_name", read_only=True
    )

    class Meta:
        model = Student
        fields = (
            "student_id",
            "user",
            "roll_no",
            "branch_name",
            "total_due_books",
            "profile",
        )

    def get_student_name(self, obj):
        usr = User.objects.get(user_id=obj.user.user_id)
        user = usr.get_full_name()
        return user

    '''For adding Student.'''
    def save(self, validated_data, password):
        uname = random.randint(100, 999)
        name = validated_data["name"].split(" ")
        username = str(name[0]) + str(name[-1]) + str(uname)
        email_lower = validated_data["email"].lower()
        user = User.objects.create_user(username=username,
                                 email=email_lower,
                                 password=password,
                                 first_name=name[0],
                                 last_name=name[-1], mobile_no=validated_data["mobile_no"])
        stu = Student.objects.create(
            roll_no=validated_data["roll_no"],
            branch_name=validated_data.get("branch_name"),
            total_due_books=validated_data.get("total_due_books"),
        )

        usr = User.objects.get(user_id=user.user_id)
        stu.user = usr
        stu.save()
        return stu.user.user_id


class BorrowerSerializer(serializers.ModelSerializer):
    student = serializers.SerializerMethodField(
        method_name="get_student_name", read_only=True
    )
    book = serializers.CharField(source="book.title", default="Book-Title")

    class Meta:
        model = Borrower
        fields = (
            "borrower_id",
            "student",
            "book",
            "issue_date",
            "return_date",
        )

    def get_student_name(self, obj):
        student = User.objects.get(user_id=obj.student.user.user_id)
        student = student.get_full_name()
        return student