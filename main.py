from PyPDF2.errors import PdfReadError
from PyPDF2._reader import PdfReader
from globals import expense_map
import matplotlib.pyplot as plt
import numpy as np
import re
import os
import traceback


txn_start = '$ Amount'
txn_end = 'Total fees charged'


def generate_pdf_reader():
    """
    This method generates an instance of PDFReader and returns it back for the provided input
    file name
    :return: PDFReader reader
    """
    files = os.listdir('stmt')
    file_name = ''
    for f in files:
        # Fetch the first file
        file_name = 'stmt/'+f
        break
    file_obj = open(file_name, 'rb')
    reader = PdfReader(file_obj)
    print(f'File being processed {file_name.split("/")[-1]}')
    print(f'Total Pages: {len(reader.pages)}')
    return reader


def fetch_contents():
    """
    This function will read the contents of the first file from stmt directory, parse the lines
    and return it back
    :return: List contents
    """
    files = os.listdir('stmt')
    file_name = ''
    for f in files:
        # Fetch the first file
        file_name = 'stmt/' + f
        print(f'Processing file {file_name}')
        break
    with open(file_name, 'r') as f:
        contents = f.readlines()
    f.close()
    return contents


def parse_stmt_date(transactions: list):
    """
    This function parses the transaction lines and finds the statement start-end date for the
    final expense report
    :param transactions: List of string
    :return: string of date range
    """
    for txn in transactions:
        if re.findall("\d{2}\/\d{2}\/\d{2}\s\-\s\d{2}\/\d{2}\/\d{2}", txn):
            stmt_dates = re.findall("\d{2}\/\d{2}\/\d{2}\s\-\s\d{2}\/\d{2}\/\d{2}", txn)
            return stmt_dates


def parse_transactions(reader, transactions: list):
    """
    This method reads all the pages from the provided reader, extracts the text and filters
    credit card transactions before adding them to a list and returning the list of transactions
    :param reader: PdfReader object
    :param transactions: List of string
    :return: List split_transactions
    """
    split_transactions = []
    if reader is not None:
        for page_num in range(len(reader.pages)):
            try:
                page_content = reader.pages[page_num]
                transactions = page_content.extract_text()
                if transactions.find(txn_start) > 0:
                    txn_found = True
                    raw_transactions = transactions[transactions.find(txn_start) + len(txn_start):
                                                    transactions.find(txn_end)]
                    split_transactions.extend(raw_transactions.splitlines())
            except PdfReadError as e:
                print(f'Error when reading Page#{page_num+1}: {e}')
                traceback.print_exc()
    else:
        # Return incoming transactions as the txt file is already split into lines
        split_transactions = transactions
        print(split_transactions)
    return split_transactions


def plot_expenses(expenses_tot: dict, s_dates: str):
    """
    This function will generate a pie chart with the provided Total expenses
    :param expenses_tot: Dict of total expenses
    :param s_dates: String of statement date
    """
    stats_tot = np.array(list(expenses_tot.values()))
    stats_cat = np.array(list(expenses_tot.keys()))
    explosion = [0.1] * len(list(expenses_tot.keys()))
    plt.pie(stats_tot, labels=stats_cat, explode=explosion, shadow=True,
            autopct=lambda x: '{:.2f}'.format(x*stats_tot.sum()/100))
    plt.title(f'Expense Report for Statement: {s_dates[0]}\n')
    plt.show()


def categorize_transactions(transactions: list):
    """
    This functions takes the list of transactions, finds the lines which are valid transaction
    lines i.e. those lines that have an amount associated with it as mentioned in the regex
    :param transactions: list of string
    :return:
    """
    expenses = dict()
    expenses_classified = dict()
    for txn in transactions:
        # Filter transactions which have a date and no negatives i.e. payments
        if re.findall("\d+\/\d+", txn) and not re.findall("-\d+\.\d+", txn) \
                and (re.findall("\d+\.\d+", txn) or re.findall("\.\d+", txn)):
            # Parsing the amount from txn using one of the formats as specified
            amount = re.findall("\d+\,\d+\.\d+", txn) or re.findall("\d+\.\d+", txn) \
                     or re.findall("\.\d+", txn)
            for expense_category, expense_values in expense_map.items():
                if any(val.lower() in txn.lower() for val in expense_values):
                    if expense_category not in expenses:
                        expenses_classified[expense_category] = list()
                        # Replace commas for number > 999
                        expenses[expense_category] = round(float(amount[0].replace(',', '')), 2)
                    else:
                        # Replace commas for number > 999
                        expenses[expense_category] = round(expenses[expense_category]
                                                           + float(amount[0].replace(',', '')), 2)
                    expenses_classified[expense_category].append(txn)
                    break
    print('\n')
    print('*'*50)
    print('DETAILED EXPENSES')
    print('*'*50)
    for category, txn in expenses_classified.items():
        print(category)
        print(*txn)
    print('\n')
    print('*' * 50)
    print('TOTAL EXPENSES')
    print('*' * 50)
    print(expenses)
    return expenses


if __name__ == '__main__':
    # Problem with PyPDF2 since end of file cannot be determined on some pages
    # pdf_reader = generate_pdf_reader()
    file_contents = fetch_contents()
    dates = parse_stmt_date(file_contents)
    cc_transactions = parse_transactions(None, file_contents)
    expenses_all = categorize_transactions(cc_transactions)
    plot_expenses(expenses_all, dates)

