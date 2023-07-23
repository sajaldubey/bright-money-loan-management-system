from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .serializers import CustomerSerializer, LoanSerializer, TransactionSerializer
from .models import Customer, Loan, Transaction, LoanDetails
from json import JSONDecodeError
from django.http import JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
import math
from datetime import datetime
from dateutil.relativedelta import relativedelta
from .tasks import get_credit_score


# POST api - api/register-user
# POST api - api/apply-loan
# POST api - api/make-payment
# GET api - api/get-statement


# register user api
class CustomerView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        content = {"message": "Hello, World!"}
        return Response(content)

    def post(self, request):
        try:
            data = JSONParser().parse(request)

            serializer = CustomerSerializer(data=data)
            if serializer.is_valid(raise_exception=True):
                customer = Customer.objects.create(
                    name=data["name"],
                    email_id=data["email_id"],
                    aadhar_id=data["aadhar_id"],
                    annual_income=data["annual_income"],
                )

                # ASYNC CELERY TASK
                get_credit_score.delay(customer.id)

                response_data = {
                    "id": customer.id,
                    "message": "User registered successfully",
                }
                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                error_message = serializer.errors
                return Response(
                    {"error": error_message}, status=status.HTTP_400_BAD_REQUEST
                )
        except JSONDecodeError:
            return JsonResponse(
                {"result": "error", "message": "Json decoding error"},
                status=status.HTTP_400_BAD_REQUEST,
            )


# Apply loan api
class LoanApplicationView(APIView):

    """
    EMI Formula Reference - forbes.com
    (p * r * (1+r)^n)/((1+r)^n -1)
    """

    def post(self, request):
        LOAN_CATEGORIES = {
            "car": 750000,
            "home": 8500000,
            "educational": 5000000,
            "personal": 1000000,
        }
        try:
            data = JSONParser().parse(request)
            serializer = LoanSerializer(data=data)  # modify ser.
            if serializer.is_valid(raise_exception=True):
                customer_id = data["unique_user_id"]
                loan_type = data["loan_type"]
                principal_amount = data["loan_amount"]
                interest_rate = data["interest_rate"]
                loan_term = data["term_period"]
                disbursal_date = data["disbursement_date"]

                if interest_rate < 14:
                    return Response(
                        {"error": "Interest rate should be greater than 14%"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                try:
                    customer = Customer.objects.get(id=customer_id)
                except Customer.DoesNotExist:
                    return Response(
                        {"error": "Customer does not exist"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if customer.credit_score < 450 or customer.credit_score is None:
                    return Response(
                        {"error": "Credit Score is low or does not exist"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                elif customer.annual_income < 150000:
                    return Response(
                        {"error": "Customer's annual income is lesser than Rs. 150000"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if loan_type.lower() in LOAN_CATEGORIES.keys():
                    if principal_amount > LOAN_CATEGORIES[loan_type.lower()]:
                        return Response(
                            {
                                "error": "Requested Loan amount is higher for selected category"
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                else:
                    return Response(
                        {"error": "Invalid Loan Type"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # EMI Formula Reference - forbes.com
                # (p * r * (1+r)^n)/((1+r)^n -1)

                rate = (interest_rate / 12) / 100
                emi_amount = (
                    principal_amount * rate * math.pow((1 + rate), loan_term)
                ) / (math.pow((1 + rate), loan_term) - 1)

                monthly_emi = round(emi_amount, 2)
                toal_recoverable_amount = monthly_emi * loan_term

                if monthly_emi > (0.6 * customer.annual_income):
                    return Response(
                        {"error": "EMI amount exceeds 60% of annual income"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if (monthly_emi - (principal_amount / loan_term)) < 10000:
                    return Response(
                        {"error": "Interest earned is less than Rs. 10000"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                disbursal_date_dtf = datetime.strptime(disbursal_date, "%d-%m-%Y")
                emi_start_date = disbursal_date_dtf + relativedelta(day=1, months=1)

                emi_amount_list = list()
                emi_due_date_list = list()
                due_dates = list()

                # Ideal EMI List
                for i in range(loan_term - 1):
                    emi_amount_list.append(monthly_emi)
                    emi_due_date_list.append(
                        emi_start_date + relativedelta(day=1, months=i)
                    )
                    due_dates.append(
                        {
                            "date": emi_start_date + relativedelta(day=1, months=i),
                            "amount_due": monthly_emi,
                        },
                    )

                emi_amount_list.append(toal_recoverable_amount - sum(emi_amount_list))
                emi_due_date_list.append(
                    emi_start_date + relativedelta(day=1, months=loan_term - 1)
                )

                due_dates.append(
                    {
                        "date": emi_start_date
                        + relativedelta(day=1, months=loan_term - 1),
                        "amount_due": toal_recoverable_amount - sum(emi_amount_list),
                    },
                )

                loan = Loan.objects.create()
                loan_details = LoanDetails.objects.create(
                    loan_id=loan.id,
                )

                response = {
                    "loan_id": loan.id,
                    "due_dates": due_dates,
                }

                return Response(response, status=status.HTTP_200_OK)
            else:
                error_message = serializer.errors
                return Response(
                    {"error": error_message}, status=status.HTTP_400_BAD_REQUEST
                )
        except JSONDecodeError:
            return JsonResponse(
                {"result": "error", "message": "Json decoding error"},
                status=status.HTTP_400_BAD_REQUEST,
            )


# make payment api
class LoanPaymentView(APIView):
    def post(self, request):
        try:
            data = JSONParser().parse(request)

            serializer = LoanSerializer(data=data)  # modif ser.
            if serializer.is_valid(raise_exception=True):
                try:
                    loan = Loan.objects.get(id=data["loan_id"])
                    loan_details = LoanDetails.objects.get(loan_id=data["loan_id"])
                except Loan.DoesNotExist:
                    return Response(
                        {"error": "Invalid Loan Id"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                except LoanDetails.DoesNotExist:
                    return Response(
                        {"error": "Invalid Loan Id"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                today = datetime.datetime.now()
                last_txn = loan_details.last_transaction_date

                if (
                    last_txn.strftime("%m") == today.month
                    and last_txn.strftime("%Y") == today.year
                ):
                    return Response(
                        {"error": "Payment already made"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                elif (today - last_txn).month > 1:
                    return Response(
                        {"error": "Cant accept payment as it is overdue"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                payment_amount = data["amount"]
                customer = loan.customer

                transaction = Transaction.objects.create(
                    payment=payment_amount,
                    customer=customer,
                    loan=loan,
                    paymennt_date=today,
                )

                if payment_amount != loan_details.next_emi_amount:
                    rate = (loan.interest_rate / 12) / 100
                    emi_amount = (
                        (loan.remaining_amount - payment_amount)
                        * rate
                        * math.pow((1 + rate), loan.loan_term)
                    ) / (math.pow((1 + rate), loan.loan_term) - 1)
                    loan_details.next_emi_amount = emi_amount

                loan_details.last_transaction_date = today
                loan_details.next_emi_date = today + relativedelta(day=1, months=1)
                loan_details.total_emis_left -= 1

                if loan_details.total_emis_left == 0:
                    loan_details.is_active = False

                loan_details.save()

                response_data = {
                    "loan_id": loan.id,
                    "message": "Payment successfully received",
                }
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                error_message = serializer.errors
                return Response(
                    {"error": error_message}, status=status.HTTP_400_BAD_REQUEST
                )
        except JSONDecodeError:
            return JsonResponse(
                {"result": "error", "message": "Json decoding error"},
                status=status.HTTP_400_BAD_REQUEST,
            )


# get statement api
class LoanStatementView(APIView):
    def post(self, request):
        try:
            data = JSONParser().parse(request)

            serializer = CustomerSerializer(data=data)
            if serializer.is_valid(raise_exception=True):
                try:
                    loan = Loan.objects.get(id=data["loan_id"])
                except Loan.DoesNotExist:
                    return Response(
                        {"error": "Loan doesnt exist"}, status=status.HTTP_201_CREATED
                    )

                loan_details = LoanDetails.objects.get(loan_id=loan.id)
                if loan_details.is_active is False:
                    return Response(
                        {"error": "Loan is not in Active State"},
                        status=status.HTTP_201_CREATED,
                    )
                customer_transactions = Transaction.objects.filter(
                    customer_id=loan.customer.id,
                    loan_id=loan.id,
                )

                upcoming = []

                if len(customer_transactions) == 0:
                    return Response(
                        {
                            "past_transactions": [],
                            "upcoming_transactions": upcoming,
                        },
                        status=status.HTTP_200_OK,
                    )
                past_transactions = []
                for txn in customer_transactions:
                    past_txn = {}
                    past_txn["date"] = txn.payment_date
                    past_txn["amount_paid"] = txn.payment
                    past_txn["interest"] = loan.interest_rate
                    past_txn["principal"] = txn.remaining_amount

                    past_transactions.append(past_txn)

                response = {
                    "past_transactions": past_transactions,
                    "upcoming_transactions": upcoming,
                }

                return Response(response, status=status.HTTP_200_OK)
            else:
                error_message = serializer.errors
                return Response(
                    {"error": error_message}, status=status.HTTP_400_BAD_REQUEST
                )
        except JSONDecodeError:
            return JsonResponse(
                {"result": "error", "message": "Json decoding error"},
                status=status.HTTP_400_BAD_REQUEST,
            )
