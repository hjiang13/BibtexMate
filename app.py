import os
import requests
from flask import Flask, request, render_template, session
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session management

# Set up basic logging
logging.basicConfig(level=logging.INFO)

COUNTER_FILE = 'visit_counter.txt'

def init_counter():
    if not os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, 'w') as f:
            f.write('0')

def get_visit_count():
    with open(COUNTER_FILE, 'r') as f:
        count = int(f.read().strip())
    return count

def increment_visit_count():
    count = get_visit_count() + 1
    with open(COUNTER_FILE, 'w') as f:
        f.write(str(count))
    return count

def search_crossref_for_bibtex(title):
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
                    bibtex_url = f"https://doi.org/{doi}"
                    bibtex_response = requests.get(bibtex_url, headers={"Accept": "application/x-bibtex"})
                    logging.info(f"BibTeX response for '{title}': {bibtex_response.status_code} - {bibtex_response.text}")

                    if bibtex_response.status_code == 200:
                        return bibtex_response.text
        return None
    except Exception as e:
        logging.error(f"Error in search_crossref_for_bibtex for '{title}': {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        init_counter()
        visit_count = increment_visit_count()
        
        if request.method == 'POST':
            titles = request.form.get('titles')
            if titles:
                titles_list = titles.split('\n')
                results = {}
                for title in titles_list:
                    title = title.strip()
                    if title:
                        bibtex_entry = search_crossref_for_bibtex(title)
                        if bibtex_entry:
                            results[title] = bibtex_entry
                        else:
                            results[title] = "No BibTeX entry found for this title."
                return render_template('index.html', results=results, visit_count=visit_count)
        return render_template('index.html', visit_count=visit_count)
    except Exception as e:
        logging.error(f"Error in index route: {e}")
        return render_template('index.html', error="An internal error occurred. Please try again later.", visit_count=visit_count)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
