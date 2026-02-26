import json
from decimal import Decimal, ROUND_HALF_UP
import math

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.http import HttpResponse
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
    SavingsGoalForm,
)
from .models import Transaction, MonthlyBudget
from .models import SavingsGoal, AchievementBadge


# ===== NEW HELPER FOR BUDGET EVALUATION =====
def evaluate_budget(user):
    """Return evaluation dict for the user's current monthly budget."""
    from django.utils import timezone
    from django.db.models import Sum

    today = timezone.now().date()
    month = today.month
    year = today.year

    mb = MonthlyBudget.objects.filter(user=user, month=month, year=year).first()
    budget_amount = mb.budget_amount if mb else Decimal("0.00")

    expenses = (
        Transaction.objects.filter(
            user=user,
            type=Transaction.EXPENSE,
            date__year=year,
            date__month=month,
        )
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    remaining = budget_amount - expenses
    if expenses <= budget_amount:
        status = "within_budget"
        message = "Great job! You are managing your spending well this month."
    else:
        status = "exceeded"
        message = "You have exceeded your budget."

    top_categories = []
    if status == "exceeded":
        top_qs = (
            Transaction.objects.filter(
                user=user,
                type=Transaction.EXPENSE,
                date__year=year,
                date__month=month,
            )
            .values("category")
            .annotate(total=Sum("amount"))
            .order_by("-total")[:2]
        )
        top_categories = [
            dict(Transaction.CATEGORY_CHOICES).get(i["category"], "Other")
            for i in top_qs
        ]

    return {
        "budget": budget_amount,
        "expenses": expenses,
        "remaining": remaining,
        "status": status,
        "message": message,
        "top_categories": top_categories,
    }

# ===== END BUDGET HELPER =====



# ===== NEW HELPER FUNCTION FOR SAVINGS GOAL EMI PLANNING =====
def calculate_goal_plan(goal, current_saved):
    """
    Intelligently calculate EMI plan for a savings goal.
    
    Args:
        goal: SavingsGoal instance
        current_saved: Decimal value of current savings towards goal
    
    Returns:
        dict with keys:
            - monthly_commitment: calculated/input monthly amount
            - planned_months: calculated/input number of months
            - remaining_to_save: amount still needed
            - is_feasible: whether goal can be achieved
            - expense_suggestions: list of category cuts if insufficient commitment
    """
    current_saved = Decimal(str(current_saved))
    target = Decimal(str(goal.target_amount))
    remaining = target - current_saved
    
    result = {
        "monthly_commitment": goal.monthly_commitment or Decimal("0.00"),
        "planned_months": goal.planned_months or 0,
        "remaining_to_save": max(remaining, Decimal("0.00")),
        "is_feasible": False,
        "expense_suggestions": [],
        "standard_emi_options": []  # 3, 6, 9, 12 months options
    }
    
    if remaining <= 0:
        result["is_feasible"] = True
        result["planned_months"] = 0
        result["monthly_commitment"] = Decimal("0.00")
        return result
    
    # ===== If user provided planned_months, calculate monthly_commitment =====
    if goal.planned_months and goal.planned_months > 0:
        try:
            monthly_needed = remaining / Decimal(str(goal.planned_months))
            result["monthly_commitment"] = monthly_needed.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            result["planned_months"] = goal.planned_months
            result["is_feasible"] = True
        except Exception:
            pass
    
    # ===== If user provided monthly_commitment, calculate planned_months =====
    elif goal.monthly_commitment and goal.monthly_commitment > 0:
        try:
            commitment_decimal = Decimal(str(goal.monthly_commitment))
            months_needed = math.ceil(float(remaining / commitment_decimal))
            result["monthly_commitment"] = goal.monthly_commitment
            result["planned_months"] = months_needed
            result["is_feasible"] = True
        except Exception:
            pass
    
    # ===== Generate standard EMI options (3, 6, 9, 12 months) =====
    for months in [3, 6, 9, 12]:
        try:
            # FIX: Convert months to string first to avoid Decimal InvalidOperation
            emi = (remaining / Decimal(str(months))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            result["standard_emi_options"].append({
                "months": months,
                "monthly_commitment": emi
            })
        except Exception:
            # Fallback: skip if calculation fails
            pass
    
    # ===== INTELLIGENT SUGGESTION: Analyze expenses if insufficient commitment =====
    if result["monthly_commitment"] > 0 and goal.user:
        # Check top 2 expense categories
        top_expenses = (
            Transaction.objects.filter(user=goal.user, type=Transaction.EXPENSE)
            .values("category")
            .annotate(total=Sum("amount"))
            .order_by("-total")[:2]
        )
        
        # If we have expense data, suggest cuts
        if top_expenses:
            for top_expense in top_expenses:
                try:
                    category_name = dict(Transaction.CATEGORY_CHOICES).get(top_expense["category"], "Other")
                    category_total = Decimal(str(top_expense["total"]))
                    
                    # Suggest 10% and 20% reduction
                    cut_10_percent = (category_total * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    cut_20_percent = (category_total * Decimal("0.20")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    
                    result["expense_suggestions"].append({
                        "category": category_name,
                        "current_total": category_total,
                        "cut_10_percent": cut_10_percent,
                        "cut_20_percent": cut_20_percent,
                        "remaining_after_10": category_total - cut_10_percent,
                        "remaining_after_20": category_total - cut_20_percent,
                    })
                except Exception:
                    pass
    
    return result
# ===== END HELPER FUNCTION =====




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

    # REMOVED: Monthly budget calculations (monthly_budget, budget_amount, month_expenses, budget_usage_percentage, budget_exceeded)

    smart_form = SmartSpendingForm()
    advisor_result = None
    advisor_status = None

    # projection feature removed
    # (previous month and projection variables no longer used)

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

    # projection calculations removed; no longer applicable

    latest_transactions = user_transactions.select_related("user")[:5]
    # form for modal goal creation
    try:
        goal_form = SavingsGoalForm()
    except Exception:
        goal_form = None
    # base context (keeps core values separate from computed analytics)
    # evaluate budget for new feature
    budget_eval = evaluate_budget(request.user)

    base_context = {
        "income_total": income_total,
        "expense_total": expense_total,
        "current_balance": current_balance,
        # keep the new evaluation dict
        "budget_eval": budget_eval,
        "smart_form": smart_form,
        "advisor_result": advisor_result,
        "advisor_status": advisor_status,
        "latest_transactions": latest_transactions,
        "form": goal_form,
    }

    # --- Advanced Financial Intelligence ---
    from decimal import getcontext
    from datetime import date, timedelta

    getcontext().prec = 6

    today_date = today
    # helper: last n months boundaries
    def month_start(year, month):
        return date(year, month, 1)

    def previous_month(year, month, n=1):
        y = year
        m = month - n
        while m <= 0:
            m += 12
            y -= 1
        return y, m

    # gather last 3 and 6 months transactions
    last_3_months = []
    last_6_months = []
    for i in range(1, 7):
        y, m = previous_month(year, month, i)
        last_6_months.append((y, m))
    last_3_months = last_6_months[:3]

    def sum_for_month(y, m, ttype=None):
        qs = user_transactions.filter(date__year=y, date__month=m)
        if ttype:
            qs = qs.filter(type=ttype)
        return qs.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    # month-over-month and 3-month rolling averages
    monthly_incomes = []
    monthly_expenses = []
    for (y, m) in last_3_months:
        monthly_incomes.append(sum_for_month(y, m, Transaction.INCOME))
        monthly_expenses.append(sum_for_month(y, m, Transaction.EXPENSE))
    def rolling_avg(values):
        cleaned_values = [v for v in values if v is not None]
        if not cleaned_values:
            return Decimal("0.00")

        try:
            avg = sum(cleaned_values, Decimal("0.00")) / Decimal(len(cleaned_values))
            return avg.quantize(Decimal("0.01"))
        except Exception:
            return Decimal("0.00")
    
    # REMOVED: Predicted balance calculations (predicted_income, predicted_expense, predicted_balance, mom_change)

    # top 3 spending categories
    top_categories_qs = (
        user_transactions.filter(type=Transaction.EXPENSE)
        .values("category")
        .annotate(total=Sum("amount"))
        .order_by("-total")[:3]
    )
    top_categories = [ (dict(Transaction.CATEGORY_CHOICES).get(i['category'], 'Other'), float(i['total'])) for i in top_categories_qs ]

    # abnormal transactions ( > 150% of category average)
    abnormal = []
    from django.db.models import Avg
    category_avgs = (
        user_transactions.filter(type=Transaction.EXPENSE)
        .values("category")
        .annotate(avg=Avg("amount"))
    )
    cat_avg_map = {c['category']: (c['avg'] or Decimal('0.00')) for c in category_avgs}
    for t in user_transactions.filter(type=Transaction.EXPENSE).order_by("-amount")[:50]:
        avg = cat_avg_map.get(t.category, Decimal("0.00"))
        if avg and t.amount > (avg * Decimal("1.5")):
            abnormal.append({"id": t.id, "amount": t.amount, "category": t.get_category_display(), "date": t.date, "reason": "High relative to category average"})

    # spending spikes detection (daily spikes)
    spikes = []
    daily_totals = (
        user_transactions.filter(type=Transaction.EXPENSE)
        .values("date")
        .annotate(total=Sum("amount"))
        .order_by("-total")[:30]
    )
    if daily_totals:
        avg_daily = sum([d['total'] for d in daily_totals]) / Decimal(len(daily_totals))
        for d in daily_totals:
            if d['total'] > (avg_daily * Decimal("1.5")):
                spikes.append({"date": d['date'], "total": d['total']})

    # Financial Health Score calculation (0-100)
    # Components weights: savings_rate (30), expense_ratio (20), budget_discipline (20), consistency (15), over_budget_freq (15)
    health_score = Decimal("0.00")
    suggestions = []

    # savings rate
    total_income_all = user_transactions.filter(type=Transaction.INCOME).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    total_expense_all = user_transactions.filter(type=Transaction.EXPENSE).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    savings = total_income_all - total_expense_all
    savings_rate = Decimal("0.00")
    if total_income_all and total_income_all > Decimal("0.00"):
        savings_rate = (savings / total_income_all) * Decimal("100.0")
    # normalized to 0-30
    score_savings = min(max(savings_rate, Decimal("0.0")), Decimal("30.0")) * Decimal("0.3")

    # expense-to-income: lower is better
    expense_ratio = Decimal("100.0")
    if total_income_all and total_income_all > Decimal("0.00"):
        expense_ratio = (total_expense_all / total_income_all) * Decimal("100.0")
    # map to 0-20 where lower ratio gives higher score
    score_expense = max(Decimal("0.0"), (Decimal("100.0") - expense_ratio)) * Decimal("0.2")

    # budget discipline: proportion of months within budget in last 6 months
    budgets_checked = 0
    budgets_within = 0
    for (y, m) in last_6_months:
        mb = MonthlyBudget.objects.filter(user=request.user, year=y, month=m).first()
        if mb:
            budgets_checked += 1
            exp = user_transactions.filter(type=Transaction.EXPENSE, date__year=y, date__month=m).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
            if exp <= mb.budget_amount:
                budgets_within += 1
    budget_discipline = Decimal("0.0")
    if budgets_checked:
        budget_discipline = (Decimal(budgets_within) / Decimal(budgets_checked)) * Decimal("100.0")
    score_budget = (budget_discipline / Decimal("100.0")) * Decimal("20.0")

    # consistency: months with at least one transaction
    months_with_tx = 0
    months_total = 6
    for (y, m) in last_6_months:
        if user_transactions.filter(date__year=y, date__month=m).exists():
            months_with_tx += 1
    consistency = (Decimal(months_with_tx) / Decimal(months_total)) * Decimal("100.0")
    score_consistency = (consistency / Decimal("100.0")) * Decimal("15.0")

    # over-budget frequency: penalize for months over budget
    over_budget = Decimal(budgets_checked - budgets_within) if budgets_checked else Decimal("0.0")
    over_budget_freq = (over_budget / (Decimal(budgets_checked) if budgets_checked else Decimal(1))) * Decimal("100.0")
    # lower is better, so invert to score out of 15
    score_over_budget = max(Decimal("0.0"), (Decimal("100.0") - over_budget_freq)) / Decimal("100.0") * Decimal("15.0")

    health_score = (score_savings + score_expense + score_budget + score_consistency + score_over_budget).quantize(Decimal("0.01"))

    # color coding
    health_color = "danger"
    health_label = "Poor"
    if health_score >= 80:
        health_color = "success"
        health_label = "Excellent"
    elif health_score >= 60:
        health_color = "primary"
        health_label = "Good"
    elif health_score >= 40:
        health_color = "warning"
        health_label = "Average"

    # suggestions based on weak components
    if score_savings < Decimal("6.0"):
        suggestions.append("Increase monthly savings: target at least 10-20% of income.")
    if score_budget < Decimal("8.0"):
        suggestions.append("Set or adjust monthly budgets and review top spending categories.")
    if score_consistency < Decimal("8.0"):
        suggestions.append("Track transactions consistently every month to improve insights.")
    if score_over_budget < Decimal("8.0"):
        suggestions.append("Reduce frequency of overspending months; automate small savings.")

    # ===== UPDATED GOAL INTELLIGENCE - NO AUTO-ACHIEVEMENT =====
    # Pick active goal if any (only if not manually completed)
    active_goal = SavingsGoal.objects.filter(
        user=request.user, 
        end_date__gte=today_date,
        is_completed=False  # NEW: Only show active, non-completed goals
    ).order_by("end_date").first()
    
    goal_info = None
    if active_goal:
        # Compute current saved towards goal period
        saved = (
            user_transactions.filter(type=Transaction.INCOME, date__gte=active_goal.start_date)
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        ) - (
            user_transactions.filter(type=Transaction.EXPENSE, date__gte=active_goal.start_date)
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )
        saved = Decimal(str(saved))
        
        # ===== NEW: Check if sufficient balance without auto-completing =====
        has_sufficient = active_goal.has_sufficient_balance(saved)
        
        # ===== NEW: Use helper to calculate EMI plan =====
        goal_plan = calculate_goal_plan(active_goal, saved)
        
        goal_info = {
            "name": active_goal.name,
            "target": active_goal.target_amount,
            "current_saved": saved,
            "days_remaining": active_goal.days_remaining,
            "progress_pct": float((saved / active_goal.target_amount * Decimal('100.0')) if active_goal.target_amount and active_goal.target_amount > 0 else Decimal('0.0')),
            # ===== NEW FIELDS =====
            "has_sufficient_balance": has_sufficient,  # Show message instead of auto-complete
            "remaining_to_save": goal_plan["remaining_to_save"],
            "monthly_commitment": goal_plan["monthly_commitment"],
            "planned_months": goal_plan["planned_months"],
            "standard_emi_options": goal_plan["standard_emi_options"],  # 3, 6, 9, 12 months
            "expense_suggestions": goal_plan["expense_suggestions"],  # Category cut recommendations
            # ===== END NEW FIELDS =====
        }
    # ===== END UPDATED GOAL INTELLIGENCE =====

    # Award simple badges
    def award_badge_if_needed(user, badge_key):
        if not AchievementBadge.objects.filter(user=user, badge=badge_key).exists():
            AchievementBadge.objects.create(user=user, badge=badge_key)

    # Savings Champion: average savings rate >= 15%
    try:
        if savings_rate >= Decimal("15.0"):
            award_badge_if_needed(request.user, AchievementBadge.SAVINGS_CHAMPION)
    except Exception:
        pass

    # Budget Master: within budget for last 3 checked months
    try:
        if budgets_checked and budgets_within >= min(3, budgets_checked):
            award_badge_if_needed(request.user, AchievementBadge.BUDGET_MASTER)
    except Exception:
        pass

    # Expense Reducer: last-month expense < previous-month expense by >=10%
    try:
        if len(monthly_expenses) >= 2 and monthly_expenses[0] < monthly_expenses[1] * Decimal("0.9"):
            award_badge_if_needed(request.user, AchievementBadge.EXPENSE_REDUCER)
    except Exception:
        pass

    badges = AchievementBadge.objects.filter(user=request.user)

    insights = []
    # Build a few natural insights
    # REMOVED: Month-over-month expense change insight (mom_change)
    if top_categories:
        insights.append(f"Top spending categories: {', '.join([c[0] for c in top_categories])}.")
    if spikes:
        insights.append(f"Detected {len(spikes)} spending spikes in recent data.")
    if abnormal:
        insights.append(f"{len(abnormal)} transactions appear unusually large for their category.")

    # computed analytics context
    computed_context = {
        "health_score": float(health_score),
        "health_color": health_color,
        "health_label": health_label,
        "health_suggestions": suggestions,
        # REMOVED: predicted_income, predicted_expense, predicted_balance, financial_risk
        "goal_info": goal_info,
        "badges": badges,
        "insights": insights,
        "top_categories": top_categories,
        "abnormal_transactions": abnormal,
        "spikes": spikes,
    }

    # merge base and computed contexts for final render
    final_context = {**base_context, **computed_context}
    return render(request, "tracker/dashboard.html", final_context)



class SavingsGoalCreateView(LoginRequiredMixin, CreateView):
    model = SavingsGoal
    form_class = None
    template_name = "tracker/goal_form.html"
    success_url = reverse_lazy("tracker:dashboard")

    def get_form_class(self):
        from .forms import SavingsGoalForm

        return SavingsGoalForm

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Savings goal created successfully.")
        return super().form_valid(form)





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
        user=request.user, month=month, year=year,
        defaults={"budget_amount": Decimal("0.00")},
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

