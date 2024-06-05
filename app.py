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
        text += page.get_text("text")
    return text

def find_references_section(text):
    start_headings = ["References", "Bibliography", "Works Cited", "Literature Cited"]
    end_headings = ["Appendix", "Author Biographies", "About the Authors"]

    start = None
    end = None

    for heading in start_headings:
        pattern = re.compile(r'\b' + re.escape(heading) + r'\b', re.IGNORECASE)
        match = pattern.search(text)
        if match:
            start = match.start()
            break

    if start is not None:
        for heading in end_headings:
            pattern = re.compile(r'\b' + re.escape(heading) + r'\b', re.IGNORECASE)
            match = pattern.search(text, start)
            if match:
                end = match.start()
                break

    return text[start:end] if start is not None else ""

def extract_references(references_text):
    references = re.split(r'\n(?:\d+\.|[\[\(]\d+[\]\)])\s+', references_text)
    return [ref.strip() for ref in references if len(ref.strip()) > 10]

def extract_reference_details(ref):
    first_author = "Unknown"
    year = "n.d."
    title = "Unknown"

    author_match = re.search(r'([A-Z][a-z]+),?\s+[A-Z]\.', ref)
    if author_match:
        first_author = author_match.group(1)

    year_match = re.search(r'\b(19|20)\d{2}\b', ref)
    if year_match:
        year = year_match.group(0)

    title_match = re.search(r'“([^”]+)', ref)
    if title_match:
        title = title_match.group(1).split()[0]
    else:
        title_match = re.search(r'^[A-Z][a-z]+\s+\d{4}\.\s+(.*?)\.', ref, re.MULTILINE)
        if title_match:
            title = title_match.group(1).split()[0]

    return first_author, year, title

def format_references_as_bibtex(references):
    bibtex_entries = []
    for i, ref in enumerate(references):
        first_author, year, title = extract_reference_details(ref)
        bibtex_key = f"{first_author}{year}{title}"

        if 'doi' in ref.lower():
            entry_type = '@article'
        elif 'conference' in ref.lower() or 'proceedings' in ref.lower():
            entry_type = '@inproceedings'
        elif 'book' in ref.lower():
            entry_type = '@book'
        else:
            entry_type = '@misc'
        
        bibtex_entry = f"{entry_type}{{{bibtex_key},\n  note = {{{ref}}}\n}}"
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
            if references_text:
                references = extract_references(references_text)
                bibtex_entries = format_references_as_bibtex(references)
                return render_template('index.html', bibtex_entries=bibtex_entries)
            else:
                return render_template('index.html', error="References section not found.")
    return render_template('index.html')

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
