import os
import requests
from flask import Flask, request, render_template
import logging

app = Flask(__name__)

# Set up basic logging
logging.basicConfig(level=logging.INFO)

def search_crossref_for_reference(title, format):
    try:
        url = "https://api.crossref.org/works"
        headers = {"Accept": "application/json"}
        params = {"query.title": title, "rows": 1}

        response = requests.get(url, headers=headers, params=params)
        logging.info(f"Title search response for '{title}': {response.status_code} - {response.json()}")

        if response.status_code == 200:
            data = response.json()
            if data["message"]["items"]:
                item = data["message"]["items"][0]
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

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        titles = request.form.get('titles')
        format = request.form.get('format')
        if titles and format:
            results = process_search(titles, format)
            return render_template('index.html', results=results, format=format)
    return render_template('index.html')

@app.route('/bibtex', methods=['POST'])
def bibtex_search():
    titles = request.form.get('titles')
    if titles:
        results = process_search(titles, "BibTeX")
        return render_template('index.html', results=results, format="BibTeX")
    return render_template('index.html')

@app.route('/ris', methods=['POST'])
def ris_search():
    titles = request.form.get('titles')
    if titles:
        results = process_search(titles, "RIS")
        return render_template('index.html', results=results, format="RIS")
    return render_template('index.html')

@app.route('/vancouver', methods=['POST'])
def vancouver_search():
    titles = request.form.get('titles')
    if titles:
        results = process_search(titles, "Vancouver")
        return render_template('index.html', results=results, format="Vancouver")
    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
