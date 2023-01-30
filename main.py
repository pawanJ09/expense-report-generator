from PyPDF2.errors import PdfReadError
from PyPDF2._reader import PdfReader

txn_start = '$ Amount'
txn_end = 'Total fees charged'


def generate_pdf_reader(file_name : str):
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


if __name__ == '__main__':
    input_file = 'stmt/20221224-statements-2577-.pdf'
    pdf_reader = generate_pdf_reader(input_file)
    cc_transactions = parse_transactions(pdf_reader)
    [print(x) for x in cc_transactions]
