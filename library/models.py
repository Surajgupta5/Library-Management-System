import random
import uuid

from django.contrib import auth
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

# Create your models here.
from django.utils.safestring import mark_safe

from libraryMgntSystem.validators import EmailValidator


class BaseModel(models.Model):
    created_by = models.CharField(
        max_length=50, null=True, blank=True, help_text="username"
    )
    updated_by = models.CharField(
        max_length=25, null=True, blank=True, help_text="username"
    )
    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False, help_text="Used for Soft Delete")

    class Meta:
        abstract = True


class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, mobile_no, email, password, **extra_fields):
        """
        Create and save a user with the given mobile_no, email, and password.
        """
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(mobile_no=mobile_no, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, mobile_no, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(mobile_no, email, password, **extra_fields)

    def create_superuser(self, mobile_no, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(mobile_no, email, password, **extra_fields)

    def with_perm(
            self, perm, is_active=True, include_superusers=True, backend=None, obj=None
    ):
        if backend is None:
            backends = auth._get_backends(return_tuples=True)
            if len(backends) == 1:
                backend, _ = backends[0]
            else:
                raise ValueError(
                    "You have multiple authentication backends configured and "
                    "therefore must provide the `backend` argument."
                )
        elif not isinstance(backend, str):
            raise TypeError(
                "backend must be a dotted import path string (got %r)." % backend
            )
        else:
            backend = auth.load_backend(backend)
        if hasattr(backend, "with_perm"):
            return backend.with_perm(
                perm,
                is_active=is_active,
                include_superusers=include_superusers,
                obj=obj,
            )
        return self.none()


class User(AbstractUser, BaseModel):
    REQUIRED_FIELDS = ["mobile_no"]
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=30, blank=True, null=True)
    mobile_no = models.CharField(max_length=15, unique=True, null=True)
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    USERNAME_FIELD = "email"

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    objects = CustomUserManager()

    def get_email(self):
        email_field_name = self.get_email_field_name()
        return getattr(self, email_field_name, None)

    def set_email(self, new_mail):
        email_field_name = self.get_email_field_name()
        return setattr(self, email_field_name, new_mail)

    def get_full_name(self):
        return " ".join(
            name for name in [self.first_name, self.last_name] if name
        )


class Book(BaseModel):
    book_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.CharField(max_length=100)
    title = models.CharField(max_length=20, null=True, blank=True)
    total_copies = models.IntegerField()
    available_copies = models.IntegerField()
    summary = models.TextField(null=True, blank=True, help_text="Enter a brief description of the book")
    book_thumbnail = models.CharField(max_length=300, null=True, blank=True)

    def __str__(self):
        return self.title

    def book_thumb(self):
        return mark_safe('<a href="{}" target="_"><img src="{}" target="_" width="100"/></a>'.format(self.book_thumbnail, self.book_thumbnail))

    book_thumb.short_description = 'Image'
    book_thumb.allow_tags = True


class Student(BaseModel):
    user = models.ForeignKey(
        "User", related_name="student", on_delete=models.CASCADE
    )
    roll_no = models.CharField(max_length=10,unique=True)
    branch_name = models.CharField(max_length=10)
    total_due_books=models.IntegerField(default=0)
    profile = models.CharField(max_length=300, null=True, blank=True)

    def __str__(self):
        return self.roll_no

    def save(self, **kwargs):
        prefix = 'STD-'
        self.roll_no = (prefix + self.roll_no)
        super(Student, self).save(**kwargs)

    def profile_thumb(self):
        return mark_safe('<a href="{}" target="_"><img src="{}" target="_" width="100"/></a>'.format(self.profile, self.profile))

    profile_thumb.short_description = 'Image'
    profile_thumb.allow_tags = True

class Borrower(BaseModel):
    borrower_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    book = models.ForeignKey('Book', on_delete=models.CASCADE)
    issue_date = models.DateTimeField(null=True,blank=True)
    return_date = models.DateTimeField(null=True,blank=True)

    def __str__(self):
        return self.student.user.get_full_name()+" borrowed "+self.book.title + " on " + str(self.issue_date)

    # def save(self, **kwargs):
    #     print("datetime.datetime.today()----->", type(datetime.datetime.now().date()), type(self.return_date.date()))
    #     if self.book.id and self.student.id:
    #         bk = Book.objects.get(id=self.book.id)
    #         bk.available_copies -=1
    #         bk.save()
    #     elif self.issue_date.date() <= self.return_date.date() <= datetime.datetime.now().date():
    #         bk = Book.objects.get(id=self.book.id)
    #         bk.available_copies += 1
    #         bk.save()

