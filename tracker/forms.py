from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Transaction, MonthlyBudget


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

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
    year = forms.IntegerField(
        required=False,
        min_value=2000,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "placeholder": "Year (e.g. 2026)"}
        ),
    )

