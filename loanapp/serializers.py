from rest_framework import serializers
from .models import Customer, Loan, LoanDetail


class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ("loan_type", "interest_rate")


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ("name", "email_id", "annual_income", "aadhar_id")


class LoanDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanDetail
        fields = ["loan_id"]
