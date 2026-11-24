from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("accounts/", views.accounts, name="accounts"),
    path("transfers/", views.transfers, name="transfers"),
    path("checking-savings/", views.checking_savings, name="checking_savings"),
    path("transactions/", views.transactions, name="transactions"),
    path("loans/", views.loans, name="loans"),
    path("upgrade/", views.upgrade, name="upgrade"),
    path("security/", views.security, name="security"),
    path("reports/", views.reports, name="reports"),
    path("settings/", views.settings_page, name="settings"),
]
