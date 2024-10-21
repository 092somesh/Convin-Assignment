from django.urls import path
from .views import (
    home,
    login_view,
    create_user,
    add_expense,
    user_expenses,
    overall_expenses,
    balance_sheet,  # Make sure balance_sheet is defined in views.py
    download_balance_sheet
)

urlpatterns = [
    path('', home, name='home'),
    path('login/', login_view, name='login'),
    path('create_user/', create_user, name='create_user'),
    path('expenses/', add_expense, name='add_expense'),
    path('expenses/user/<int:user_id>/', user_expenses, name='user_expenses'),
    path('expenses/overall/', overall_expenses, name='overall_expenses'),
    path('expenses/balance-sheet/', balance_sheet, name='balance_sheet'),
    path('download-balance-sheet/', download_balance_sheet, name='download_balance_sheet'),
]
