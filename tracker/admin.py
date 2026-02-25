from django.contrib import admin

from .models import Transaction, MonthlyBudget
from .models import SavingsGoal, AchievementBadge


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "type", "category", "amount", "date", "created_at")
    list_filter = ("type", "category", "date", "user")
    search_fields = ("user__username", "description")
    date_hierarchy = "date"
    ordering = ("-date", "-created_at")


@admin.register(MonthlyBudget)
class MonthlyBudgetAdmin(admin.ModelAdmin):
    list_display = ("user", "month", "year", "budget_amount")
    list_filter = ("year", "month", "user")
    search_fields = ("user__username",)
    ordering = ("-year", "-month")


@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "target_amount", "start_date", "end_date", "created_at")
    list_filter = ("start_date", "end_date", "user")
    search_fields = ("user__username", "name")
    ordering = ("-created_at",)


@admin.register(AchievementBadge)
class AchievementBadgeAdmin(admin.ModelAdmin):
    list_display = ("user", "badge", "awarded_at")
    list_filter = ("badge", "user")
    search_fields = ("user__username",)
    ordering = ("-awarded_at",)

