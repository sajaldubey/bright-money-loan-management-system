# Bright Money Loan Management System
```
The Project uses Django Rest Framework to run API endpoints.
Used celery to process Asynchronous tasks with the help of RabbitMQ as message broker.
Imp-lemented Token Authentication with DRF
Implemented 4 api endpoints to register a new user, process a loan application, process payments made against each EMI & to fetch loan statements.
Used Celery to calculate Credit Score on the fly.
Covered almost every conditional logic for loan application as mentioned in the assigment problem statement.
```

### Screenshots
#### Register User API
![image](https://github.com/sajaldubey/bright-money-loan-management-system/assets/55424712/6020537b-9783-469b-b0eb-a8984d289e49)

#### Apply Loan API 
![image](https://github.com/sajaldubey/bright-money-loan-management-system/assets/55424712/cb3c563e-2868-449d-8384-88ed078b4d0c)


#### Make Payment API
![image](https://github.com/sajaldubey/bright-money-loan-management-system/assets/55424712/60075068-b703-4b68-ae42-6a5b122300a8)

#### Get Statement API
![image](https://github.com/sajaldubey/bright-money-loan-management-system/assets/55424712/7158416c-477b-4830-bbcf-317414766e0c)

Create a virtual environment and install all dependencies from requirements.txt file

```
pip install -r requirements.txt
```

#### The project has following features - 
> Uses Celery for Async tasks
>
> RabbitMQ service as message broker
>
> Apis to register user, apply loan, make payment & ask for statement

## Please note to install & start RabbitMQ server in the machine

#### Command to Start Celery
```
celery -A loan_management_system worker -l info
```

#### Applying Migrations
```
python manage.py makemigrations
python manage.py migrate
```

#### Create Superuser
```
python manage.py createsuperuser
```

## Please note to add a Authentication Token in request header
```
python manage.py drf_create_token <superuser username>
```

#### Run Django Server
```
python manage.py runserver
```

#### API Endpoints
```
POST - api/register-user/
POST - api/apply-loan/
POST - api/make-payment/
GET  - api/get-statement/
```

