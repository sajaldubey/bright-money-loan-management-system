from django.urls import path, re_path
from loanapp.views import (
    CustomerView,
    LoanApplicationView,
    LoanPaymentView,
    LoanStatementView,
)

urlpatterns = [
    path("register-user/", CustomerView.as_view(), name="register_user"),
    path("apply-loan/", LoanApplicationView.as_view(), name="apply_loan"),
    path("make-payment/", LoanPaymentView.as_view(), name="make_payment"),
    path("get-statement/", LoanStatementView.as_view(), name="get_statement"),
]
