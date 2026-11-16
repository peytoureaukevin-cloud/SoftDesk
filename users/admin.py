from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class SoftDeskUserAdmin(UserAdmin):
    """Affiche les champs SoftDesk dans l'administration Django."""

    fieldsets = UserAdmin.fieldsets + (
        (
            "SoftDesk et RGPD",
            {
                "fields": (
                    "age",
                    "can_be_contacted",
                    "can_data_be_shared",
                    "created_time",
                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "SoftDesk et RGPD",
            {
                "fields": (
                    "age",
                    "can_be_contacted",
                    "can_data_be_shared",
                )
            },
        ),
    )
    readonly_fields = UserAdmin.readonly_fields + ("created_time",)
