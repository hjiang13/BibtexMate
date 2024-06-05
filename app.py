import fitz  # PyMuPDF
import re
import os
import requests
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

def search_crossref_for_bibtex(reference):
    url = "https://api.crossref.org/works"
    headers = {"Accept": "application/json"}
    params = {"query.bibliographic": reference, "rows": 1}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["message"]["items"]:
            item = data["message"]["items"][0]
            doi = item.get("DOI")
            if doi:
                bibtex_url = f"https://doi.org/{doi}"
                bibtex_response = requests.get(bibtex_url, headers={"Accept": "application/x-bibtex"})
                if bibtex_response.status_code == 200:
                    return bibtex_response.text
    return None

def format_references_as_bibtex(references):
    bibtex_entries = []
    for ref in references:
        bibtex_entry = search_crossref_for_bibtex(ref)
        if bibtex_entry:
            bibtex_entries.append(bibtex_entry)
        else:
            bibtex_entries.append(f"@misc{{,\n  note = {{{ref}}}\n}}")
    return bibtex_entries

@app.route('/', methods=['GET', 'POST'])
def index():
    try:
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
    except Exception as e:
        print(f"Error in index route: {e}")
        return render_template('index.html', error="An internal error occurred. Please try again later.")

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
