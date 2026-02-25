from django.urls import path

from . import views

app_name = "tracker"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("goals/add/", views.SavingsGoalCreateView.as_view(), name="goal_add"),
    path("transactions/add/", views.TransactionCreateView.as_view(), name="transaction_add"),
    path(
        "transactions/<int:pk>/edit/",
        views.TransactionUpdateView.as_view(),
        name="transaction_edit",
    ),
    path(
        "transactions/<int:pk>/delete/",
        views.TransactionDeleteView.as_view(),
        name="transaction_delete",
    ),
    path("budget/", views.manage_budget, name="manage_budget"),
    path("reports/", views.reports, name="reports"),
]

