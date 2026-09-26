"""Back-office registration for developers and super admins (not the staff UI)."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .forms import UserAdminChangeForm, UserAdminCreationForm
from .models import StaffProfile, StudentProfile, User


class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    extra = 0


class StaffProfileInline(admin.StackedInline):
    model = StaffProfile
    can_delete = False
    extra = 0


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    inlines = [StudentProfileInline, StaffProfileInline]

    ordering = ("email",)
    list_display = ("email", "full_name", "role", "is_active", "is_suspended", "is_staff")
    list_filter = ("role", "is_active", "is_suspended", "is_staff", "is_superuser")
    search_fields = ("email", "full_name")
    readonly_fields = ("last_login", "date_joined")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("full_name",)}),
        (
            "Access",
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_suspended",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "full_name",
                    "role",
                    "usable_password",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
