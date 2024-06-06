import os
import requests
from flask import Flask, request, render_template, send_file
import logging
from io import StringIO

app = Flask(__name__)

# Set up basic logging
logging.basicConfig(level=logging.INFO)

def normalize_title(title):
    return title.lower().strip()

def is_exact_match(input_title, returned_title):
    return normalize_title(input_title) == normalize_title(returned_title)

def search_crossref_for_reference(title, format):
    try:
        url = "https://api.crossref.org/works"
        headers = {"Accept": "application/json"}
        params = {"query.title": title, "rows": 10}

        response = requests.get(url, headers=headers, params=params)
        logging.info(f"Title search response for '{title}': {response.status_code} - {response.json()}")

        if response.status_code == 200:
            data = response.json()
            for item in data["message"]["items"]:
                returned_title = item.get("title", [""])[0]
                if is_exact_match(title, returned_title):
                    doi = item.get("DOI")
                    if doi:
                        if format == "BibTeX":
                            ref_url = f"https://doi.org/{doi}"
                            ref_headers = {"Accept": "application/x-bibtex"}
                        elif format == "RIS":
                            ref_url = f"https://doi.org/{doi}"
                            ref_headers = {"Accept": "application/x-research-info-systems"}
                        elif format == "Vancouver":
                            ref_url = f"https://doi.org/{doi}"
                            ref_headers = {"Accept": "text/x-bibliography; style=vancouver"}
                        elif format == "MLA":
                            ref_url = f"https://doi.org/{doi}"
                            ref_headers = {"Accept": "text/x-bibliography; style=mla"}

                        ref_response = requests.get(ref_url, headers=ref_headers)
                        logging.info(f"Reference response for '{title}': {ref_response.status_code} - {ref_response.text}")

                        if ref_response.status_code == 200:
                            return ref_response.text
        return None
    except Exception as e:
        logging.error(f"Error in search_crossref_for_reference for '{title}': {e}")
        return None

def process_search(titles, format):
    results = {}
    titles_list = titles.split('\n')
    for title in titles_list:
        title = title.strip()
        if title:
            ref_entry = search_crossref_for_reference(title, format)
            if ref_entry:
                results[title] = ref_entry
            else:
                results[title] = f"No {format} entry found for this title."
    return results

def generate_file_content(results, format):
    file_content = ""
    for title, ref in results.items():
        file_content += f"{ref}\n\n"
    return file_content

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        titles = request.form.get('titles')
        format = request.form.get('format')
        if titles and format:
            results = process_search(titles, format)
            file_content = generate_file_content(results, format)
            file_name = f"references.{format.lower()}.txt"
            with open(file_name, "w") as file:
                file.write(file_content)
            return render_template('index.html', results=results, format=format, file_name=file_name)
    return render_template('index.html')

@app.route('/download/<file_name>')
def download_file(file_name):
    return send_file(file_name, as_attachment=True)

@app.route('/bibtex', methods=['POST'])
def bibtex_search():
    titles = request.form.get('titles')
    if titles:
        results = process_search(titles, "BibTeX")
        file_content = generate_file_content(results, "BibTeX")
        file_name = "references.bibtex.txt"
        with open(file_name, "w") as file:
            file.write(file_content)
        return render_template('index.html', results=results, format="BibTeX", file_name=file_name)
    return render_template('index.html')

@app.route('/ris', methods=['POST'])
def ris_search():
    titles = request.form.get('titles')
    if titles:
        results = process_search(titles, "RIS")
        file_content = generate_file_content(results, "RIS")
        file_name = "references.ris.txt"
        with open(file_name, "w") as file:
            file.write(file_content)
        return render_template('index.html', results=results, format="RIS", file_name=file_name)
    return render_template('index.html')

@app.route('/vancouver', methods=['POST'])
def vancouver_search():
    titles = request.form.get('titles')
    if titles:
        results = process_search(titles, "Vancouver")
        file_content = generate_file_content(results, "Vancouver")
        file_name = "references.vancouver.txt"
        with open(file_name, "w") as file:
            file.write(file_content)
        return render_template('index.html', results=results, format="Vancouver", file_name=file_name)
    return render_template('index.html')

@app.route('/mla', methods=['POST'])
def mla_search():
    titles = request.form.get('titles')
    if titles:
        results = process_search(titles, "MLA")
        file_content = generate_file_content(results, "MLA")
        file_name = "references.mla.txt"
        with open(file_name, "w") as file:
            file.write(file_content)
        return render_template('index.html', results=results, format="MLA", file_name=file_name)
    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
