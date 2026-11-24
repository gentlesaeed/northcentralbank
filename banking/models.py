import secrets
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


def generate_account_number():
    return f"{secrets.randbelow(900000) + 100000}"


class Profile(models.Model):
    class Tier(models.TextChoices):
        BASIC = "Basic", "Basic"
        PLUS = "Plus", "Plus"
        PREMIER = "Premier", "Premier"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account_tier = models.CharField(
        max_length=12, choices=Tier.choices, default=Tier.BASIC
    )
    two_factor_preference = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} profile"


class Account(models.Model):
    class AccountType(models.TextChoices):
        CHECKING = "Checking", "Checking"
        SAVINGS = "Savings", "Savings"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="accounts"
    )
    number = models.CharField(
        max_length=6, unique=True, default=generate_account_number, editable=False
    )
    holder_name = models.CharField(max_length=120)
    account_type = models.CharField(max_length=10, choices=AccountType.choices)
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.number} · {self.holder_name}"


class Transaction(models.Model):
    class Kind(models.TextChoices):
        OPENING_DEPOSIT = "Opening deposit", "Opening deposit"
        TRANSFER = "Transfer", "Transfer"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions"
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    source_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="outgoing_transactions",
        null=True,
        blank=True,
    )
    destination_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="incoming_transactions"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.kind}: {self.amount} ({self.created_at:%Y-%m-%d})"


class LoanApplication(models.Model):
    class LoanType(models.TextChoices):
        PERSONAL = "Personal loan", "Personal loan"
        HOME = "Home improvement", "Home improvement"
        AUTO = "Auto loan", "Auto loan"

    class Status(models.TextChoices):
        SUBMITTED = "Submitted", "Submitted"
        IN_REVIEW = "In review", "In review"
        DECLINED = "Declined", "Declined"

    class Term(models.IntegerChoices):
        TWELVE = 12, "12 months"
        TWENTY_FOUR = 24, "24 months"
        THIRTY_SIX = 36, "36 months"
        SIXTY = 60, "60 months"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="loan_applications"
    )
    loan_type = models.CharField(max_length=24, choices=LoanType.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    purpose = models.CharField(max_length=240)
    term_months = models.PositiveSmallIntegerField(choices=Term.choices)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.SUBMITTED
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_loan_type_display()} request · {self.user}"


class UpgradeRequest(models.Model):
    class Tier(models.TextChoices):
        PLUS = "Plus", "Plus"
        PREMIER = "Premier", "Premier"

    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        APPROVED = "Approved", "Approved"
        DECLINED = "Declined", "Declined"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="upgrade_requests"
    )
    requested_tier = models.CharField(max_length=12, choices=Tier.choices)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(status="Pending"),
                name="one_pending_upgrade_per_user",
            )
        ]

    def __str__(self):
        return f"{self.user} · {self.requested_tier} ({self.status})"
