from django.contrib import admin
from django.contrib.admin import register
from library.models import Book, User, Student, Borrower

base = {
    'fields': (('created_by', 'updated_by'), 'updated_at',
               'is_deleted',),
    'classes': ('collapse',),
}

@register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ["book_id", "title", "author", "book_thumb", "available_copies", "is_deleted"]
    readonly_fields = ('book_thumb',)
    fieldsets = (
        ('Book', {
            'fields': (('title', 'author'), ('total_copies', 'available_copies'), 'summary', "book_thumbnail")
        }),
        ('Base', base),
    )


@register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["user_id", "first_name", "last_name", "email", "is_deleted"]
    fieldsets = (
        ('User', {
            'fields': (('first_name', 'last_name'), ('email', 'password'), ('mobile_no', 'username'), 'groups')
        }),
        ('Base', base),
    )


@register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "roll_no", "branch_name", "profile_thumb", "is_deleted"]
    fieldsets = (
        ('Student', {
            'fields': (('user', 'roll_no'), ('branch_name', 'total_due_books'), 'profile')
        }),
        ('Base', base),
    )

@register(Borrower)
class BorrowerAdmin(admin.ModelAdmin):
    list_display = ["borrower_id", "student", "book", "issue_date"]
    fieldsets = (
        ('Borrower', {
            'fields': (('student', 'book'), ('issue_date', 'return_date'))
        }),
        ('Base', base),
    )