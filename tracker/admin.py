from django.contrib import admin

from .models import Comment, Contributor, Issue, Project


class ContributorInline(admin.TabularInline):
    model = Contributor
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["title", "type", "author", "created_time"]
    list_filter = ["type"]
    search_fields = ["title", "author__username"]
    inlines = [ContributorInline]


@admin.register(Contributor)
class ContributorAdmin(admin.ModelAdmin):
    list_display = ["user", "project", "created_time"]
    search_fields = ["user__username", "project__title"]


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ["title", "project", "tag", "priority", "status", "author"]
    list_filter = ["tag", "priority", "status"]
    search_fields = ["title", "project__title", "author__username"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["id", "issue", "author", "created_time"]
    search_fields = ["description", "issue__title", "author__username"]
