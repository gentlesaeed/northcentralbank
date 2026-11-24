from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.db import IntegrityError, transaction
from django.db.models import F, Sum
from django.shortcuts import redirect, render

from .forms import (
    AccountForm,
    LoanApplicationForm,
    RegistrationForm,
    TransferForm,
    UpgradeRequestForm,
)
from .models import Account, LoanApplication, Profile, Transaction, UpgradeRequest


def home(request):
    return redirect("dashboard" if request.user.is_authenticated else "login")


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        Profile.objects.create(user=user)
        login(request, user)
        messages.success(request, "Your demo account is ready.")
        return redirect("dashboard")
    return render(request, "registration/register.html", {"form": form})


@login_required
def dashboard(request):
    accounts = Account.objects.filter(user=request.user)
    transactions = Transaction.objects.filter(user=request.user)
    total_balance = accounts.aggregate(total=Sum("balance"))["total"] or Decimal("0.00")
    context = {
        "total_balance": total_balance,
        "account_count": accounts.count(),
        "transfer_count": transactions.filter(kind=Transaction.Kind.TRANSFER).count(),
        "recent_transactions": transactions[:8],
    }
    return render(request, "banking/dashboard.html", context)


@login_required
def accounts(request):
    form = AccountForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        account = None
        for _ in range(5):
            try:
                with transaction.atomic():
                    account = Account.objects.create(
                        user=request.user,
                        holder_name=request.user.get_full_name().strip()
                        or request.user.username,
                        account_type=form.cleaned_data["account_type"],
                        balance=form.cleaned_data["opening_balance"],
                    )
                    if account.balance:
                        Transaction.objects.create(
                            user=request.user,
                            kind=Transaction.Kind.OPENING_DEPOSIT,
                            destination_account=account,
                            amount=account.balance,
                        )
                break
            except IntegrityError:
                continue
        if account is None:
            messages.error(request, "Could not create an account. Please try again.")
        else:
            messages.success(request, f"{account.get_account_type_display()} account created.")
            return redirect("accounts")
    return render(
        request,
        "banking/accounts.html",
        {"form": form, "accounts": Account.objects.filter(user=request.user)},
    )


@login_required
def transfers(request):
    form = TransferForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        source = form.cleaned_data["source_account"]
        destination = form.cleaned_data["destination_account"]
        amount = form.cleaned_data["amount"]
        with transaction.atomic():
            debited = Account.objects.filter(
                pk=source.pk, user=request.user, balance__gte=amount
            ).update(balance=F("balance") - amount)
            if not debited:
                form.add_error("amount", "The source account does not have enough funds.")
            else:
                Account.objects.filter(pk=destination.pk, user=request.user).update(
                    balance=F("balance") + amount
                )
                Transaction.objects.create(
                    user=request.user,
                    kind=Transaction.Kind.TRANSFER,
                    source_account_id=source.pk,
                    destination_account_id=destination.pk,
                    amount=amount,
                )
        if not form.errors:
            messages.success(request, "Your transfer was recorded in the demo ledger.")
            return redirect("transactions")
    return render(request, "banking/transfers.html", {"form": form})


@login_required
def checking_savings(request):
    accounts = Account.objects.filter(user=request.user)
    totals = {
        Account.AccountType.CHECKING: accounts.filter(
            account_type=Account.AccountType.CHECKING
        ).aggregate(total=Sum("balance"))["total"]
        or Decimal("0.00"),
        Account.AccountType.SAVINGS: accounts.filter(
            account_type=Account.AccountType.SAVINGS
        ).aggregate(total=Sum("balance"))["total"]
        or Decimal("0.00"),
    }
    form = TransferForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        source = form.cleaned_data["source_account"]
        destination = form.cleaned_data["destination_account"]
        amount = form.cleaned_data["amount"]
        if source.account_type == destination.account_type:
            form.add_error(
                "destination_account",
                "Choose one checking account and one savings account.",
            )
        else:
            with transaction.atomic():
                debited = Account.objects.filter(
                    pk=source.pk, user=request.user, balance__gte=amount
                ).update(balance=F("balance") - amount)
                if not debited:
                    form.add_error("amount", "The source account does not have enough funds.")
                else:
                    Account.objects.filter(pk=destination.pk, user=request.user).update(
                        balance=F("balance") + amount
                    )
                    Transaction.objects.create(
                        user=request.user,
                        kind=Transaction.Kind.TRANSFER,
                        source_account_id=source.pk,
                        destination_account_id=destination.pk,
                        amount=amount,
                    )
            if not form.errors:
                messages.success(request, "Your transfer was recorded in the demo ledger.")
                return redirect("checking_savings")
    return render(
        request,
        "banking/checking_savings.html",
        {"accounts": accounts, "totals": totals, "form": form},
    )


@login_required
def transactions(request):
    return render(
        request,
        "banking/transactions.html",
        {"transactions": Transaction.objects.filter(user=request.user)},
    )


@login_required
def loans(request):
    form = LoanApplicationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if not Account.objects.filter(
            user=request.user, account_type=Account.AccountType.CHECKING
        ).exists():
            form.add_error(None, "Create a checking account before requesting a demo loan.")
        else:
            application = form.save(commit=False)
            application.user = request.user
            application.save()
            messages.success(
                request,
                "Request submitted for review. This demo does not perform credit checks or approve loans.",
            )
            return redirect("loans")
    return render(
        request,
        "banking/loans.html",
        {
            "form": form,
            "applications": LoanApplication.objects.filter(user=request.user),
        },
    )


@login_required
def upgrade(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    form = UpgradeRequestForm(request.POST or None)
    balance = Account.objects.filter(user=request.user).aggregate(total=Sum("balance"))[
        "total"
    ] or Decimal("0.00")
    if request.method == "POST" and form.is_valid():
        target = form.cleaned_data["requested_tier"]
        thresholds = {"Plus": Decimal("5000.00"), "Premier": Decimal("25000.00")}
        tier_order = {
            Profile.Tier.BASIC: 0,
            Profile.Tier.PLUS: 1,
            Profile.Tier.PREMIER: 2,
        }
        if tier_order[target] <= tier_order[profile.account_tier]:
            form.add_error("requested_tier", "Choose a tier above your current tier.")
        elif balance < thresholds[target]:
            form.add_error(
                "requested_tier",
                f"This illustrative demo tier requires a ${thresholds[target]:,.2f} balance.",
            )
        elif not Account.objects.filter(
            user=request.user, account_type=Account.AccountType.CHECKING
        ).exists():
            form.add_error("requested_tier", "Create a checking account before requesting an upgrade.")
        elif UpgradeRequest.objects.filter(
            user=request.user, status=UpgradeRequest.Status.PENDING
        ).exists():
            form.add_error("requested_tier", "You already have an upgrade request pending.")
        else:
            try:
                UpgradeRequest.objects.create(user=request.user, requested_tier=target)
            except IntegrityError:
                form.add_error("requested_tier", "You already have an upgrade request pending.")
            else:
                messages.success(
                    request,
                    f"{target} upgrade request submitted. Tier changes require review.",
                )
                return redirect("upgrade")
    return render(
        request,
        "banking/upgrade.html",
        {
            "form": form,
            "profile": profile,
            "balance": balance,
            "requests": UpgradeRequest.objects.filter(user=request.user),
        },
    )


@login_required
def security(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    password_form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and "change_password" in request.POST:
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was updated.")
            return redirect("security")
    if request.method == "POST" and "save_security" in request.POST:
        profile.two_factor_preference = request.POST.get("two_factor_preference") == "on"
        profile.save(update_fields=["two_factor_preference"])
        messages.success(request, "Your demo security preference was saved.")
        return redirect("security")
    return render(
        request,
        "banking/security.html",
        {"profile": profile, "password_form": password_form},
    )


@login_required
def reports(request):
    accounts = Account.objects.filter(user=request.user)
    total_balance = accounts.aggregate(total=Sum("balance"))["total"] or Decimal("0.00")
    total_transferred = Transaction.objects.filter(
        user=request.user, kind=Transaction.Kind.TRANSFER
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    return render(
        request,
        "banking/reports.html",
        {
            "accounts": accounts,
            "total_balance": total_balance,
            "total_transferred": total_transferred,
            "transaction_count": Transaction.objects.filter(user=request.user).count(),
        },
    )


@login_required
def settings_page(request):
    return render(request, "banking/settings.html")
