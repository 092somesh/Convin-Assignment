from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from .models import Expense, Income, Split  # Assuming you have Expense, Income, and Split models
import csv

def home(request):
    return render(request, 'home.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  # Redirect to home after successful login
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')  # Render login page for GET requests

def create_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')  # Add email if needed

        # Validate user input
        if not username or not password:
            return render(request, 'create_user.html', {'error': 'Username and password are required'})

        try:
            user = User.objects.create_user(username=username, password=password, email=email)
            return redirect('home')
        except IntegrityError:
            return render(request, 'create_user.html', {'error': 'Username already exists'})

    return render(request, 'create_user.html')

def add_expense(request):
    if request.method == 'POST':
        description = request.POST.get('description')
        amount = request.POST.get('amount')
        split_method = request.POST.get('split_method')
        user_id = request.POST.get('user')  # This is the user selected from the form

        # Validate input
        if not description or not amount or not user_id:
            return render(request, 'add_expense.html', {'error': 'All fields are required', 'users': User.objects.all()})

        try:
            user = User.objects.get(id=user_id)
            amount = float(amount)  # Ensure amount is a float

            # Create the expense first
            expense = Expense.objects.create(description=description, amount=amount, user=user)

            # Handle the split method
            if split_method == 'equal':
                users = User.objects.exclude(id=user_id)  # Exclude the user who created the expense
                split_amount = amount / users.count() if users.count() > 0 else 0

                for u in users:
                    Split.objects.create(expense=expense, user=u, method='equal', share=split_amount)

            elif split_method == 'exact':
                users = User.objects.exclude(id=user_id)  # Exclude the user who created the expense
                for u in users:
                    share = request.POST.get(f'share_{u.id}')  # Example input names like "share_1", "share_2", etc.
                    if share:
                        try:
                            share = float(share)
                            Split.objects.create(expense=expense, user=u, method='exact', share=share)
                        except (ValueError, TypeError):
                            continue  # Ignore invalid shares

            elif split_method == 'percentage':
                users = User.objects.exclude(id=user_id)  # Exclude the user who created the expense
                for u in users:
                    percentage = request.POST.get(f'percentage_{u.id}')  # Example input names like "percentage_1", etc.
                    if percentage:
                        try:
                            percentage = float(percentage)
                            share = (percentage / 100) * amount
                            Split.objects.create(expense=expense, user=u, method='percentage', share=share)
                        except (ValueError, TypeError):
                            continue  # Ignore invalid percentages

            return redirect('user_expenses', user_id=user.id)

        except ObjectDoesNotExist:
            return render(request, 'add_expense.html', {'error': 'User does not exist', 'users': User.objects.all()})
        except ValueError:
            return render(request, 'add_expense.html', {'error': 'Invalid amount', 'users': User.objects.all()})

    users = User.objects.all()
    return render(request, 'add_expense.html', {'users': users})

def user_expenses(request, user_id):
    try:
        expenses = Expense.objects.filter(user_id=user_id)
        user = User.objects.get(id=user_id)  # Handle case if user does not exist
        return render(request, 'user_expenses.html', {'expenses': expenses, 'user': user})
    except ObjectDoesNotExist:
        return render(request, 'user_expenses.html', {'error': 'User does not exist'})

def overall_expenses(request):
    expenses = Expense.objects.all()
    return render(request, 'overall_expenses.html', {'expenses': expenses})

import pandas as pd
from django.http import HttpResponse
from .models import Expense, Split

def download_balance_sheet(request):
    # Create a list to hold the balance sheet data
    data = []

    expenses = Expense.objects.all()
    print(f"Expenses found: {len(expenses)}")  # Debug: Check how many expenses are found
    for expense in expenses:
        splits = Split.objects.filter(expense=expense)
        print(f"Splits for expense {expense.id} ({expense.description}): {len(splits)}")  # Debug: Check splits count

        for split in splits:
            data.append({
                'User': split.user.username,
                'Description': expense.description,
                'Amount': expense.amount,
                'Owed Share': split.share,
                'Date': expense.date,
            })

    # Check if any data was collected
    if not data:
        print("No data found for balance sheet.")  # Debug: Notify if no data was collected
    else:
        print("Data collected for balance sheet:", data)  # Debug: Show collected data

    # Create a DataFrame
    df = pd.DataFrame(data)

    # Create the HttpResponse object with the appropriate Excel header
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="balance_sheet.xlsx"'

    # Write the DataFrame to the response
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Balance Sheet')

    return response


# You need to define the balance_sheet function as well
def balance_sheet(request):
    # You may need to pass some context if required
    return render(request, 'expenses/balance_sheet.html')

    # Logic to gather data for the balance sheet
    # For example, you could calculate total expenses, owed shares, etc.
    expenses = Expense.objects.filter(user=request.user)  # Replace with your logic
    return render(request, 'balance_sheet.html', {'expenses': expenses})
