from django.contrib import admin
from django.urls import path

from library.views import LoginView, LogoutView, BookView, StudentView, BorrowerView, AdminRegistrationView, \
    PublicBookView, FileUpload

urlpatterns = [
    path("signup/", AdminRegistrationView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("student/", StudentView.as_view(), name="student_list"),
    path("student/<uuid:id>/", StudentView.as_view(), name="get_student"),
    path("borrower/", BorrowerView.as_view(), name="borrower_list"),
    path("borrower/<uuid:id>/", BorrowerView.as_view(), name="get_borrower"),
    path("public-books/", PublicBookView.as_view(), name="public_book_list"),
    path("book/", BookView.as_view(), name="book_list"),
    path("book/<uuid:id>/", BookView.as_view(), name="crud_book"),
    path("file_upload/", FileUpload.as_view(), name="file_upload"),

]
