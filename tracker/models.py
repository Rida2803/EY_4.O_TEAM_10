from django.conf import settings
from django.db import models
from django.utils import timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


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


class SavingsGoal(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="savings_goals",
    )
    name = models.CharField(max_length=120)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.target_amount})"

    @property
    def days_remaining(self) -> int:
        return max((self.end_date - timezone.now().date()).days, 0)

    def required_monthly_saving(self) -> Decimal:
        remaining_days = self.days_remaining
        if remaining_days <= 0:
            return Decimal("0.00")
        # compute months remaining as integer number of 30-day periods (ceil), at least 1
        months_count = max((remaining_days + 29) // 30, 1)
        # compute amount already saved towards goal
        saved = (
            self.user.transactions.filter(type=Transaction.INCOME, date__gte=self.start_date)
            .aggregate(total=models.Sum("amount"))["total"]
            or Decimal("0.00")
        ) - (
            self.user.transactions.filter(type=Transaction.EXPENSE, date__gte=self.start_date)
            .aggregate(total=models.Sum("amount"))["total"]
            or Decimal("0.00")
        )
        # normalize types to Decimal to avoid issues when values are strings
        target = Decimal(str(self.target_amount))
        saved = Decimal(saved)
        remaining = target - saved
        if remaining <= Decimal("0.00"):
            return Decimal("0.00")
        # divide by integer month count to avoid Decimal division edge-cases
        per_month = remaining / Decimal(months_count)
        try:
            return per_month.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except InvalidOperation:
            # Fallback: convert to float and round, then to Decimal
            try:
                val = float(per_month)
            except Exception:
                return Decimal("0.00")
            return Decimal(str(round(val, 2)))


class AchievementBadge(models.Model):
    SAVINGS_CHAMPION = "SAVINGS_CHAMPION"
    BUDGET_MASTER = "BUDGET_MASTER"
    EXPENSE_REDUCER = "EXPENSE_REDUCER"

    BADGE_CHOICES = [
        (SAVINGS_CHAMPION, "Savings Champion"),
        (BUDGET_MASTER, "Budget Master"),
        (EXPENSE_REDUCER, "Expense Reducer"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="badges",
    )
    badge = models.CharField(max_length=40, choices=BADGE_CHOICES)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "badge")

    def __str__(self):
        return f"{self.user.username} - {self.get_badge_display()}"

