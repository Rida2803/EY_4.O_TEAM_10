from django.conf import settings
from django.db import models
from django.utils import timezone


class Transaction(models.Model):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"

    TRANSACTION_TYPE_CHOICES = [
        (INCOME, "Income"),
        (EXPENSE, "Expense"),
    ]

    CATEGORY_FOOD = "FOOD"
    CATEGORY_TRAVEL = "TRAVEL"
    CATEGORY_RENT = "RENT"
    CATEGORY_SHOPPING = "SHOPPING"
    CATEGORY_OTHER = "OTHER"

    CATEGORY_CHOICES = [
        (CATEGORY_FOOD, "Food"),
        (CATEGORY_TRAVEL, "Travel"),
        (CATEGORY_RENT, "Rent"),
        (CATEGORY_SHOPPING, "Shopping"),
        (CATEGORY_OTHER, "Other"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.CharField(max_length=255, blank=True)
    # Use a default so the field is still editable in forms
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.type} - {self.amount}"


class MonthlyBudget(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="monthly_budgets",
    )
    month = models.PositiveSmallIntegerField()
    year = models.PositiveIntegerField()
    budget_amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ("user", "month", "year")
        ordering = ["-year", "-month"]

    def __str__(self):
        return f"{self.user.username} - {self.month}/{self.year} - {self.budget_amount}"

    @property
    def period_label(self) -> str:
        return timezone.datetime(self.year, self.month, 1).strftime("%B %Y")

