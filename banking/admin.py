from django.contrib import admin

from .models import Account, LoanApplication, Profile, Transaction, UpgradeRequest


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("number", "holder_name", "account_type", "balance", "user", "created_at")
    list_filter = ("account_type", "created_at")
    search_fields = ("number", "holder_name", "user__username")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("kind", "source_account", "destination_account", "amount", "user", "created_at")
    list_filter = ("kind", "created_at")
    search_fields = ("user__username", "source_account__number", "destination_account__number")


@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ("loan_type", "amount", "term_months", "status", "user", "created_at")
    list_filter = ("status", "loan_type")


@admin.register(UpgradeRequest)
class UpgradeRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "requested_tier", "status", "created_at")
    list_filter = ("status", "requested_tier")


admin.site.register(Profile)
