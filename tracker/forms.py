from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Transaction, MonthlyBudget, SavingsGoal


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap form-control classes to all fields for consistent alignment
        self.fields["username"].widget.attrs.update({"class": "form-control"})
        self.fields["email"].widget.attrs.update({"class": "form-control"})
        self.fields["password1"].widget.attrs.update({"class": "form-control"})
        self.fields["password2"].widget.attrs.update({"class": "form-control"})

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["amount", "type", "category", "description", "date"]
        widgets = {
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "type": forms.Select(attrs={"class": "form-select"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "description": forms.TextInput(attrs={"class": "form-control"}),
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }


class BudgetForm(forms.ModelForm):
    class Meta:
        model = MonthlyBudget
        fields = ["month", "year", "budget_amount"]
        widgets = {
            "month": forms.NumberInput(
                attrs={"min": 1, "max": 12, "class": "form-control"}
            ),
            "year": forms.NumberInput(
                attrs={"min": 2000, "class": "form-control"}
            ),
            "budget_amount": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
        }


class SmartSpendingForm(forms.Form):
    planned_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        label="Planned Spending Amount",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter amount you plan to spend",
                "step": "0.01",
            }
        ),
    )


class ReportFilterForm(forms.Form):
    month = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=12,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "placeholder": "Month (1-12)"}
        ),
    )




class SavingsGoalForm(forms.ModelForm):
    class Meta:
        model = SavingsGoal
        fields = ["name", "target_amount", "start_date", "end_date", "monthly_commitment", "planned_months"]

    def __init__(self, *args, **kwargs):
        # import model lazily to avoid circular import at module load
        from .models import SavingsGoal

        super().__init__(*args, **kwargs)
        self._meta.model = SavingsGoal
        self.fields["name"].widget.attrs.update({"class": "form-control"})
        self.fields["target_amount"].widget.attrs.update({"class": "form-control", "step": "0.01"})
        self.fields["start_date"].widget.attrs.update({"class": "form-control", "type": "date"})
        self.fields["end_date"].widget.attrs.update({"class": "form-control", "type": "date"})
        # ===== NEW FIELDS FOR EMI PLANNING =====
        self.fields["monthly_commitment"].widget.attrs.update({
            "class": "form-control",
            "step": "0.01",
            "placeholder": "Optional: Enter monthly commitment amount"
        })
        self.fields["monthly_commitment"].label = "Monthly Commitment (Optional)"
        self.fields["monthly_commitment"].required = False
        
        self.fields["planned_months"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Optional: Enter number of months"
        })
        self.fields["planned_months"].label = "Planned Months (Optional)"
        self.fields["planned_months"].required = False
        # ===== END NEW FIELDS =====
    

