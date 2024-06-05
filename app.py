import fitz  # PyMuPDF
import re
import os
from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += page.get_text()
    return text

def find_references_section(text):
    pattern = re.compile(r'(references|bibliography|works cited)', re.IGNORECASE)
    match = pattern.search(text)
    if match:
        return text[match.start():]
    return ""

def extract_references(references_text):
    references = references_text.split('\n')
    return [ref for ref in references if len(ref) > 10]

def format_references_as_bibtex(references):
    bibtex_entries = []
    for ref in references:
        if 'doi' in ref.lower():
            entry_type = '@article'
        elif 'conference' in ref.lower() or 'proceedings' in ref.lower():
            entry_type = '@inproceedings'
        else:
            entry_type = '@misc'
        bibtex_entry = f"{entry_type}{{\n  {ref}\n}}"
        bibtex_entries.append(bibtex_entry)
    return bibtex_entries

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            text = extract_text_from_pdf(filepath)
            references_text = find_references_section(text)
            references = extract_references(references_text)
            bibtex_entries = format_references_as_bibtex(references)
            return render_template('index.html', bibtex_entries=bibtex_entries)
    return render_template('index.html')

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
