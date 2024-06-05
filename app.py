import os
import requests
from flask import Flask, request, render_template, redirect, url_for
from urllib.parse import quote as url_quote

app = Flask(__name__)

def search_crossref_for_bibtex(title):
    url = "https://api.crossref.org/works"
    headers = {"Accept": "application/json"}
    params = {"query.title": title, "rows": 1}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["message"]["items"]:
            item = data["message"]["items"][0]
            doi = item.get("DOI")
            if doi:
                bibtex_url = f"https://doi.org/{url_quote(doi)}"
                bibtex_response = requests.get(bibtex_url, headers={"Accept": "application/x-bibtex"})
                if bibtex_response.status_code == 200:
                    return bibtex_response.text
    return None

@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        if request.method == 'POST':
            title = request.form.get('title')
            if title:
                bibtex_entry = search_crossref_for_bibtex(title)
                if bibtex_entry:
                    return render_template('index.html', bibtex_entry=bibtex_entry)
                else:
                    return render_template('index.html', error="No BibTeX entry found for the given title.")
        return render_template('index.html')
    except Exception as e:
        print(f"Error in index route: {e}")
        return render_template('index.html', error="An internal error occurred. Please try again later.")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
