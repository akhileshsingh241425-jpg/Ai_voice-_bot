import pdfplumber
import os

folder_path = r"C:\Users\hp\Desktop\AI traning voice boot\New folder"
pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]

for pdf_file in pdf_files:
    pdf_path = os.path.join(folder_path, pdf_file)
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ''
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'
            separator = '=' * 80
            print(f'\n{separator}')
            print(f'FILE: {pdf_file}')
            print(separator)
            print(text)
    except Exception as e:
        print(f'Error reading {pdf_file}: {e}')
