from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Account, Transaction


class BankingWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="customer", password="StrongPassword123!")
        self.client.force_login(self.user)
        self.checking = Account.objects.create(
            user=self.user,
            holder_name="Customer",
            account_type=Account.AccountType.CHECKING,
            balance=Decimal("100.00"),
        )
        self.savings = Account.objects.create(
            user=self.user,
            holder_name="Customer",
            account_type=Account.AccountType.SAVINGS,
            balance=Decimal("25.00"),
        )

    def test_transfer_moves_funds_and_records_transaction(self):
        response = self.client.post(
            reverse("transfers"),
            {
                "source_account": self.checking.pk,
                "destination_account": self.savings.pk,
                "amount": "30.00",
            },
        )

        self.assertRedirects(response, reverse("transactions"))
        self.checking.refresh_from_db()
        self.savings.refresh_from_db()
        self.assertEqual(self.checking.balance, Decimal("70.00"))
        self.assertEqual(self.savings.balance, Decimal("55.00"))
        self.assertEqual(Transaction.objects.filter(user=self.user).count(), 1)

    def test_transfer_rejects_insufficient_funds_without_changing_balances(self):
        response = self.client.post(
            reverse("transfers"),
            {
                "source_account": self.checking.pk,
                "destination_account": self.savings.pk,
                "amount": "100.01",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.checking.refresh_from_db()
        self.savings.refresh_from_db()
        self.assertEqual(self.checking.balance, Decimal("100.00"))
        self.assertEqual(self.savings.balance, Decimal("25.00"))
        self.assertFalse(Transaction.objects.exists())

    def test_customers_cannot_transfer_between_another_users_accounts(self):
        other_user = User.objects.create_user(username="other", password="StrongPassword123!")
        other_account = Account.objects.create(
            user=other_user,
            holder_name="Other",
            account_type=Account.AccountType.CHECKING,
            balance=Decimal("50.00"),
        )
        response = self.client.post(
            reverse("transfers"),
            {
                "source_account": self.checking.pk,
                "destination_account": other_account.pk,
                "amount": "10.00",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.checking.refresh_from_db()
        other_account.refresh_from_db()
        self.assertEqual(self.checking.balance, Decimal("100.00"))
        self.assertEqual(other_account.balance, Decimal("50.00"))
        self.assertFalse(Transaction.objects.exists())

    def test_registration_signs_in_new_customer(self):
        self.client.logout()
        response = self.client.post(
            reverse("register"),
            {
                "username": "new-customer",
                "first_name": "New",
                "last_name": "Customer",
                "email": "new@example.com",
                "password1": "a-very-strong-demo-password",
                "password2": "a-very-strong-demo-password",
            },
        )

        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(User.objects.filter(username="new-customer").exists())

    def test_all_customer_pages_render(self):
        page_names = (
            "dashboard",
            "accounts",
            "transfers",
            "checking_savings",
            "transactions",
            "loans",
            "upgrade",
            "security",
            "reports",
            "settings",
        )

        for page_name in page_names:
            with self.subTest(page=page_name):
                response = self.client.get(reverse(page_name))
                self.assertEqual(response.status_code, 200)

    def test_account_creation_records_opening_deposit(self):
        response = self.client.post(
            reverse("accounts"),
            {"account_type": Account.AccountType.SAVINGS, "opening_balance": "42.50"},
        )

        self.assertRedirects(response, reverse("accounts"))
        account = Account.objects.get(
            user=self.user,
            account_type=Account.AccountType.SAVINGS,
            balance=Decimal("42.50"),
        )
        self.assertEqual(account.balance, Decimal("42.50"))
        self.assertEqual(Transaction.objects.get().amount, Decimal("42.50"))
