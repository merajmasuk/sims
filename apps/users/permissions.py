from rest_framework.permissions import BasePermission

from apps.users.models import User


class IsAdmin(BasePermission):
    message = "This action requires admin privileges."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.ADMIN
        )


class IsFaculty(BasePermission):
    message = "This action requires faculty privileges."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.FACULTY
        )


class IsStudent(BasePermission):
    message = "This action requires student privileges."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.STUDENT
        )


class IsAdminOrFaculty(BasePermission):
    message = "This action requires admin or faculty privileges."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (User.Role.ADMIN, User.Role.FACULTY)
        )
