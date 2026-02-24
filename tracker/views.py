import json
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, DeleteView, UpdateView

from .forms import (
    UserRegistrationForm,
    TransactionForm,
    BudgetForm,
    SmartSpendingForm,
    ReportFilterForm,
)
from .models import Transaction, MonthlyBudget


def register(request):
    if request.user.is_authenticated:
        return redirect("tracker:dashboard")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful. Welcome!")
            return redirect("tracker:dashboard")
        messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegistrationForm()

    return render(request, "registration/register.html", {"form": form})


@login_required
def dashboard(request):
    today = timezone.now().date()
    month = today.month
    year = today.year

    user_transactions = Transaction.objects.filter(user=request.user)

    income_total = (
        user_transactions.filter(type=Transaction.INCOME).aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )
    expense_total = (
        user_transactions.filter(type=Transaction.EXPENSE).aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )
    current_balance = income_total - expense_total

    monthly_budget, _ = MonthlyBudget.objects.get_or_create(
    user=request.user,
    month=month,
    year=year,
    defaults={
        "budget_amount": Decimal("0.00")
    }
    )
    budget_amount = monthly_budget.budget_amount if monthly_budget else Decimal("0.00")

    month_expenses = user_transactions.filter(
        type=Transaction.EXPENSE, date__year=year, date__month=month
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    budget_usage_percentage = Decimal("0.00")
    budget_exceeded = False
    if budget_amount > 0:
        budget_usage_percentage = (month_expenses / budget_amount) * 100
        budget_exceeded = month_expenses > budget_amount

    smart_form = SmartSpendingForm()
    advisor_result = None
    advisor_status = None

    if request.method == "POST":
        smart_form = SmartSpendingForm(request.POST)
        if smart_form.is_valid():
            planned_amount = smart_form.cleaned_data["planned_amount"]
            remaining_balance = current_balance - planned_amount
            savings_threshold = current_balance * Decimal("0.20")

            if remaining_balance < 0:
                advisor_result = (
                    "Not Recommended: This spending would exceed your balance."
                )
                advisor_status = "danger"
            elif remaining_balance >= savings_threshold:
                advisor_result = (
                    "Safe to Spend: You will still retain at least 20% savings."
                )
                advisor_status = "success"
            else:
                advisor_result = (
                    "Warning: Low Savings. You will have less than 20% savings."
                )
                advisor_status = "warning"
        else:
            messages.error(request, "Please enter a valid planned amount.")

    latest_transactions = user_transactions.select_related("user")[:5]

    context = {
        "income_total": income_total,
        "expense_total": expense_total,
        "current_balance": current_balance,
        "monthly_budget": monthly_budget,
        "budget_usage_percentage": float(budget_usage_percentage),
        "budget_exceeded": budget_exceeded,
        "month_expenses": month_expenses,
        "smart_form": smart_form,
        "advisor_result": advisor_result,
        "advisor_status": advisor_status,
        "latest_transactions": latest_transactions,
    }

    return render(request, "tracker/dashboard.html", context)


class TransactionCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "tracker/transaction_form.html"
    success_url = reverse_lazy("tracker:dashboard")

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Transaction added successfully.")
        return super().form_valid(form)


class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "tracker/transaction_form.html"
    success_url = reverse_lazy("tracker:dashboard")

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Transaction updated successfully.")
        return super().form_valid(form)


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    template_name = "tracker/transaction_confirm_delete.html"
    success_url = reverse_lazy("tracker:dashboard")

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Transaction deleted successfully.")
        return super().delete(request, *args, **kwargs)


@login_required
def manage_budget(request):
    today = timezone.now().date()
    month = today.month
    year = today.year

    monthly_budget, _ = MonthlyBudget.objects.get_or_create(
        user=request.user, month=month, year=year
    )

    if request.method == "POST":
        form = BudgetForm(request.POST, instance=monthly_budget)
        if form.is_valid():
            form.instance.user = request.user
            form.save()
            messages.success(request, "Monthly budget saved successfully.")
            return redirect("tracker:dashboard")
        messages.error(request, "Please correct the errors below.")
    else:
        form = BudgetForm(instance=monthly_budget)

    return render(
        request,
        "tracker/budget_form.html",
        {"form": form, "month": month, "year": year},
    )


@login_required
def reports(request):
    filter_form = ReportFilterForm(request.GET or None)
    transactions = Transaction.objects.filter(user=request.user)

    selected_month = None
    selected_year = None

    if filter_form.is_valid():
        selected_month = filter_form.cleaned_data.get("month")
        selected_year = filter_form.cleaned_data.get("year")

        if selected_year:
            transactions = transactions.filter(date__year=selected_year)
        if selected_month:
            transactions = transactions.filter(date__month=selected_month)

    total_income = (
        transactions.filter(type=Transaction.INCOME).aggregate(total=Sum("amount"))[
            "total"
        ]
        or Decimal("0.00")
    )
    total_expense = (
        transactions.filter(type=Transaction.EXPENSE).aggregate(total=Sum("amount"))[
            "total"
        ]
        or Decimal("0.00")
    )

    category_data = (
        transactions.filter(type=Transaction.EXPENSE)
        .values("category")
        .annotate(total=Sum("amount"))
        .order_by("category")
    )

    category_labels = []
    category_values = []

    category_display_map = dict(Transaction.CATEGORY_CHOICES)
    for item in category_data:
        category_labels.append(category_display_map.get(item["category"], "Other"))
        category_values.append(float(item["total"]))

    income_expense_labels = ["Income", "Expense"]
    income_expense_values = [float(total_income), float(total_expense)]

    context = {
        "filter_form": filter_form,
        "total_income": total_income,
        "total_expense": total_expense,
        "category_labels_json": mark_safe(json.dumps(category_labels)),
        "category_values_json": mark_safe(json.dumps(category_values)),
        "income_expense_labels_json": mark_safe(json.dumps(income_expense_labels)),
        "income_expense_values_json": mark_safe(json.dumps(income_expense_values)),
        "selected_month": selected_month,
        "selected_year": selected_year,
        "transactions": transactions.order_by("-date", "-created_at")[:50],
    }

    return render(request, "tracker/reports.html", context)

