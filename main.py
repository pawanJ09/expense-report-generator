import PyPDF2

if __name__ == '__main__':
    fileName = 'stmt/20221224-statements-2577-.pdf'
    pdfFileObj = open(fileName, 'rb')
    pdfReader = PyPDF2.PdfReader(pdfFileObj)
    print(f'Total Pages in {fileName.split("/")[-1]}: {len(pdfReader.pages)}')