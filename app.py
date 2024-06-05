import os
import requests
from flask import Flask, request, render_template
import logging

app = Flask(__name__)

# Set up basic logging
logging.basicConfig(level=logging.INFO)

def search_crossref_for_references(title):
    try:
        url = "https://api.crossref.org/works"
        headers = {"Accept": "application/json"}
        params = {"query.title": title, "rows": 1}

        response = requests.get(url, headers=headers, params=params)
        logging.info(f"Title search response: {response.status_code} - {response.json()}")

        if response.status_code == 200:
            data = response.json()
            if data["message"]["items"]:
                item = data["message"]["items"][0]
                doi = item.get("DOI")
                if doi:
                    references_url = f"https://api.crossref.org/works/{doi}/references"
                    references_response = requests.get(references_url, headers=headers)
                    logging.info(f"References response: {references_response.status_code} - {references_response.json()}")

                    if references_response.status_code == 200:
                        references_data = references_response.json()
                        references = references_data.get("message", {}).get("reference", [])
                        logging.info(f"Found {len(references)} references")
                        return references
                    else:
                        logging.warning(f"References not found for DOI: {doi}")
            else:
                logging.warning(f"No items found for the title: {title}")
        return []
    except Exception as e:
        logging.error(f"Error in search_crossref_for_references: {e}")
        return []

@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        if request.method == 'POST':
            title = request.form.get('title')
            if title:
                references = search_crossref_for_references(title)
                if references:
                    return render_template('index.html', references=references)
                else:
                    return render_template('index.html', error="No references found for the given title.")
        return render_template('index.html')
    except Exception as e:
        logging.error(f"Error in index route: {e}")
        return render_template('index.html', error="An internal error occurred. Please try again later.")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
