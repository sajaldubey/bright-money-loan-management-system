from celery import shared_task
from .models import AccountTransaction, Customer
import logging


@shared_task
def get_credit_score(customer_id):
    try:
        customer = Customer.objects.get(id=customer_id)
        credit = sum(
            list(
                AccountTransaction.objects.filter(
                    aadhar_id=customer.aadhar_id, transaction_type="credit"
                )
            )
        )
        debit = sum(
            list(
                AccountTransaction.objects.filter(
                    aadhar_id=customer.aadhar_id, transaction_type="debit"
                )
            )
        )

        account_balance = credit - debit

        if account_balance >= 1000000:
            credit_score = 900
        elif account_balance <= 100000:
            credit_score = 300
        else:
            credit_score = 300 + (account_balance - 100000) // 15000 * 10

        customer.credit_score = credit_score
        customer.save()
    except Exception as e:
        logging.error(f"Error while calculating Credit Score.")
