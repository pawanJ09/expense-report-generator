from PyPDF2.errors import PdfReadError
from PyPDF2._reader import PdfReader
from globals import expense_map
import re

txn_start = '$ Amount'
txn_end = 'Total fees charged'


def generate_pdf_reader(file_name: str):
    """
    This method generates an instance of PDFReader and returns it back for the provided input
    file name
    :param file_name: Input file name
    :return: PDFReader reader
    """
    file_obj = open(file_name, 'rb')
    reader = PdfReader(file_obj, strict=False)
    print(f'Total Pages in {file_name.split("/")[-1]}: {len(reader.pages)}')
    return reader


def parse_transactions(reader: PdfReader):
    """
    This method reads all the pages from the provided reader, extracts the text and filters
    credit card transactions before adding them to a list and returning the list of transactions
    :param reader: PdfReader object
    :return: List of transactions
    """
    txn_found = False
    split_transactions = []
    for page_num in range(len(pdf_reader.pages)):
        try:
            page_content = pdf_reader.pages[page_num]
            transactions = page_content.extract_text()
            if (transactions.find(txn_start) > 0 and not txn_found) or txn_found:
                txn_found = True
                raw_transactions = transactions[transactions.find(txn_start) + len(txn_start):
                                                transactions.find(txn_end)]
                split_transactions.extend(raw_transactions.splitlines())
        except PdfReadError:
            txn_found = False
    return split_transactions


def categorize_transactions(transactions: list):
    expenses = dict()
    # expenses_new = dict()
    for txn in transactions:
        # Filter transactions which have a date and no negatives i.e. payments
        if re.findall("\d+\/\d+", txn) and not re.findall("-\d+\.\d+", txn) \
                and (re.findall("\d+\.\d+", txn) or re.findall("\.\d+", txn)):
            amount = re.findall("\d+\.\d+", txn)
            if not amount:
                amount = re.findall("\.\d+", txn)
            for expense_category, expense_values in expense_map.items():
                if any(val.lower() in txn.lower() for val in expense_values):
                    if expense_category not in expenses:
                        # expenses_new[expense_category] = list()
                        expenses[expense_category] = round(float(amount[0]), 2)
                    else:
                        expenses[expense_category] = round(expenses[expense_category]
                                                           + float(amount[0]), 2)
                    # expenses_new[expense_category].append(amount)
                    break
    print(expenses)
    # print(expenses_new)


if __name__ == '__main__':
    input_file = 'stmt/20221224-statements-2577-.pdf'
    pdf_reader = generate_pdf_reader(input_file)
    cc_transactions = parse_transactions(pdf_reader)
    categorize_transactions(cc_transactions)
