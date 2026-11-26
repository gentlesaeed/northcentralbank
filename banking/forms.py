from decimal import Decimal

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Account, LoanApplication, UpgradeRequest


class RegistrationForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")


class AccountForm(forms.Form):
    account_type = forms.ChoiceField(choices=Account.AccountType.choices)
    opening_balance = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00"),
        initial=Decimal("0.00"),
        help_text="Optional opening balance for this simulated account.",
    )


class TransferForm(forms.Form):
    source_account = forms.ModelChoiceField(queryset=Account.objects.none())
    destination_account = forms.ModelChoiceField(queryset=Account.objects.none())
    amount = forms.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        accounts = Account.objects.filter(user=user)
        self.fields["source_account"].queryset = accounts
        self.fields["destination_account"].queryset = accounts

    def clean(self):
        cleaned_data = super().clean()
        source = cleaned_data.get("source_account")
        destination = cleaned_data.get("destination_account")
        if source and destination and source.pk == destination.pk:
            self.add_error("destination_account", "Choose a different destination account.")
        return cleaned_data


class LoanApplicationForm(forms.ModelForm):
    class Meta:
        model = LoanApplication
        fields = ("loan_type", "amount", "purpose", "term_months")
        widgets = {
            "purpose": forms.TextInput(attrs={"placeholder": "What is the loan for?"}),
        }

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount < Decimal("500.00") or amount > Decimal("50000.00"):
            raise forms.ValidationError("Request an amount between $500 and $50,000.")
        return amount

    def clean_purpose(self):
        purpose = self.cleaned_data["purpose"].strip()
        if not purpose:
            raise forms.ValidationError("Enter a brief purpose for your request.")
        return purpose


class UpgradeRequestForm(forms.Form):
    requested_tier = forms.ChoiceField(choices=UpgradeRequest.Tier.choices)
