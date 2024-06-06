import os
import requests
from flask import Flask, request, render_template, send_file
import logging
from io import StringIO
from difflib import SequenceMatcher
import json

app = Flask(__name__)

# Set up basic logging
logging.basicConfig(level=logging.INFO)

# Initialize visit count and visitor log
visit_count = 200
visitor_log = []

def get_visitor_location(ip):
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json")
        if response.status_code == 200:
            data = response.json()
            location = data.get("city", "Unknown city") + ", " + data.get("country", "Unknown country")
            return location
    except Exception as e:
        logging.error(f"Error getting location for IP '{ip}': {e}")
    return "Unknown location"

def normalize_title(title):
    return title.lower().strip()

def is_exact_match(input_title, returned_title):
    return normalize_title(input_title) == normalize_title(returned_title)

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def search_crossref_for_reference_by_title(title, format):
    try:
        url = "https://api.crossref.org/works"
        headers = {"Accept": "application/json"}
        params = {"query.title": title, "rows": 10}

        response = requests.get(url, headers=headers, params=params)
        logging.info(f"Title search response for '{title}': {response.status_code} - {response.json()}")

        if response.status_code == 200:
            data = response.json()
            best_match = None
            best_similarity = 0.0
            for item in data["message"]["items"]:
                returned_title = item.get("title", [""])[0]
                similarity = similar(normalize_title(title), normalize_title(returned_title))
                if similarity > best_similarity:
                    best_match = item
                    best_similarity = similarity

            if best_match and best_similarity > 0.8:  # Adjust the threshold as needed
                doi = best_match.get("DOI")
                if doi:
                    return fetch_reference_by_doi(doi, format)
        return None
    except Exception as e:
        logging.error(f"Error in search_crossref_for_reference_by_title for '{title}': {e}")
        return None

def fetch_reference_by_doi(doi, format):
    try:
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
        logging.info(f"Reference response for DOI '{doi}': {ref_response.status_code} - {ref_response.text}")

        if ref_response.status_code == 200:
            return ref_response.text
        return None
    except Exception as e:
        logging.error(f"Error in fetch_reference_by_doi for DOI '{doi}': {e}")
        return None

def process_search(titles, dois, format):
    results = {}

    if titles:
        titles_list = titles.split('\n')
        for title in titles_list:
            title = title.strip()
            if title:
                ref_entry = search_crossref_for_reference_by_title(title, format)
                if ref_entry:
                    results[title] = ref_entry
                else:
                    results[title] = f"No {format} entry found for this title."

    if dois:
        dois_list = dois.split('\n')
        for doi in dois_list:
            doi = doi.strip()
            if doi:
                ref_entry = fetch_reference_by_doi(doi, format)
                if ref_entry:
                    results[doi] = ref_entry
                else:
                    results[doi] = f"No {format} entry found for this DOI."

    return results

def generate_file_content(results, format):
    file_content = ""
    for title, ref in results.items():
        file_content += f"{ref}\n\n"
    return file_content

@app.route('/', methods=['GET', 'POST'])
def index():
    global visit_count
    global visitor_log

    # Increment visit count
    visit_count += 1

    # Log visitor's IP and location
    visitor_ip = request.remote_addr
    visitor_location = get_visitor_location(visitor_ip)
    visitor_log.append({"ip": visitor_ip, "location": visitor_location})

    if request.method == 'POST':
        titles = request.form.get('titles')
        dois = request.form.get('dois')
        format = request.form.get('format')
        if (titles or dois) and format:
            results = process_search(titles, dois, format)
            file_content = generate_file_content(results, format)
            file_name = f"references.{format.lower()}.txt"
            with open(file_name, "w") as file:
                file.write(file_content)
            return render_template('index.html', results=results, format=format, file_name=file_name, visit_count=visit_count, visitor_log=visitor_log)
    return render_template('index.html', visit_count=visit_count, visitor_log=visitor_log)

@app.route('/download/<file_name>')
def download_file(file_name):
    return send_file(file_name, as_attachment=True)

@app.route('/bibtex', methods=['POST'])
def bibtex_search():
    titles = request.form.get('titles')
    dois = request.form.get('dois')
    if titles or dois:
        results = process_search(titles, dois, "BibTeX")
        file_content = generate_file_content(results, "BibTeX")
        file_name = "references.bibtex.txt"
        with open(file_name, "w") as file:
            file.write(file_content)
        return render_template('index.html', results=results, format="BibTeX", file_name=file_name, visit_count=visit_count, visitor_log=visitor_log)
    return render_template('index.html', visit_count=visit_count, visitor_log=visitor_log)

@app.route('/ris', methods=['POST'])
def ris_search():
    titles = request.form.get('titles')
    dois = request.form.get('dois')
    if titles or dois:
        results = process_search(titles, dois, "RIS")
        file_content = generate_file_content(results, "RIS")
        file_name = "references.ris.txt"
        with open(file_name, "w") as file:
            file.write(file_content)
        return render_template('index.html', results=results, format="RIS", file_name=file_name, visit_count=visit_count, visitor_log=visitor_log)
    return render_template('index.html', visit_count=visit_count, visitor_log=visitor_log)

@app.route('/vancouver', methods=['POST'])
def vancouver_search():
    titles = request.form.get('titles')
    dois = request.form.get('dois')
    if titles or dois:
        results = process_search(titles, dois, "Vancouver")
        file_content = generate_file_content(results, "Vancouver")
        file_name = "references.vancouver.txt"
        with open(file_name, "w") as file:
            file.write(file_content)
        return render_template('index.html', results=results, format="Vancouver", file_name=file_name, visit_count=visit_count, visitor_log=visitor_log)
    return render_template('index.html', visit_count=visit_count, visitor_log=visitor_log)

@app.route('/mla', methods=['POST'])
def mla_search():
    titles = request.form.get('titles')
    dois = request.form.get('dois')
    if titles or dois:
        results = process_search(titles, dois, "MLA")
        file_content = generate_file_content(results, "MLA")
        file_name = "references.mla.txt"
        with open(file_name, "w") as file:
            file.write(file_content)
        return render_template('index.html', results=results, format="MLA", file_name=file_name, visit_count=visit_count, visitor_log=visitor_log)
    return render_template('index.html', visit_count=visit_count, visitor_log=visitor_log)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
