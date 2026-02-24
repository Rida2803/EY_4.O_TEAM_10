from django.contrib import admin

from .models import Transaction, MonthlyBudget


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

