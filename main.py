from PyPDF2.errors import PdfReadError
import PyPDF2

txn_start = '$ Amount'
txn_end = 'Total fees charged'

if __name__ == '__main__':
    file_name = 'stmt/20221224-statements-2577-.pdf'
    file_obj = open(file_name, 'rb')
    pdfReader = PyPDF2.PdfReader(file_obj, strict=False)
    print(f'Total Pages in {file_name.split("/")[-1]}: {len(pdfReader.pages)}')
    txn_found = False
    split_transactions = []
    for page_num in range(len(pdfReader.pages)):
        try:
            page_content = pdfReader.pages[page_num]
            transactions = page_content.extract_text()
            if (transactions.find(txn_start) > 0 and not txn_found) or txn_found:
                txn_found = True
                raw_transactions = transactions[transactions.find(txn_start)+len(txn_start) :
                                                transactions.find(txn_end)]
                split_transactions.extend(raw_transactions.splitlines())
                [print(x) for x in split_transactions]
        except PdfReadError:
            txn_found = False
