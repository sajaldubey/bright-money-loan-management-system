from django.db import models
import uuid
import json
from django.contrib.auth.models import User
from utils.abstract_models import PrimaryKeyModel


# or can create a class with ID uuid field and inherit in other classes
# use Timestamped Model
class Customer(PrimaryKeyModel):
    # customer = models.OneToOneField(
    #     User, unique=True, on_delete=models.CASCADE, related_name="customer"
    # )
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email_id = models.EmailField()
    credit_score = models.IntegerField(null=True, blank=True)
    aadhar_id = models.UUIDField(unique=True)
    annual_income = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class AccountTransaction(models.Model):
    TRANSACTION_CHOICES = [
        ("credit", "CREDIT"),
        ("debit", "DEBIT"),
    ]
    transaction_type = models.CharField(choices=TRANSACTION_CHOICES, max_length=20)
    transaction_date = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    aadhar_id = models.UUIDField(editable=False)

    def __str__(self):
        return self.transaction_type + " - " + self.amount


class Loan(PrimaryKeyModel):
    LOAN_CATEGORIES = [
        ("Car", "Car"),
        ("Home", "Home"),
        ("Education", "Education"),
        ("Personal", "Personal"),
    ]

    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan_type = models.CharField(max_length=25, choices=LOAN_CATEGORIES)
    principal_amount = models.PositiveIntegerField()
    interest_rate = models.DecimalField(decimal_places=2, max_digits=5)
    loan_term = models.PositiveIntegerField()  # months
    disbursal_date = models.DateTimeField(auto_now=True)
    # emi = models.DecimalField(decimal_places=2, max_digits=10)
    start_date = models.DateField(auto_now=True)
    end_date = models.DateField()
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="loan_customers"
    )
    remaining_amount = models.PositiveIntegerField(default=20)

    def __str__(self):
        return self.customer + " - " + self.loan_type + " Loan"


class LoanDetails(models.Model):
    loan_id = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="loan")
    # current_transaction_amount = models.DecimalField(decimal_places=2, max_digits=10)
    last_transaction_date = models.DateTimeField(blank=True, null=True)
    next_emi_date = models.DateField()
    next_emi_amount = models.DecimalField(decimal_places=2, max_digits=10)
    initial_emi_amounts = models.CharField(max_length=1000)
    adjusted_emi_amounts = models.CharField(max_length=1000)
    total_emis_left = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def set_initial_emi_amounts(self, lst):
        self.initial_emi_amounts = json.dumps(lst)

    def get_initial_emi_amounts(self):
        return json.loads(self.initial_emi_amounts)

    def set_adjusted_emi_amounts(self, lst):
        self.adjusted_emi_amounts = json.dumps(lst)

    def get_adjusted_emi_amounts(self):
        return json.loads(self.adjusted_emi_amounts)


# Customer EMI Transactions
class Transaction(models.Model):
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.DecimalField(max_digits=10, decimal_places=2)
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="customer_transactions"
    )
    loan = models.ForeignKey(
        Loan, on_delete=models.CASCADE, related_name="loan_transactions"
    )
    payment_date = models.DateTimeField(auto_now=True)
    remaining_amount = models.DecimalField(decimal_places=2, max_digits=10, default=20)
