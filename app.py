import os
import re
import requests
from flask import Flask, request, render_template
import logging

app = Flask(__name__)

# Set up basic logging
logging.basicConfig(level=logging.INFO)

def extract_references(paragraph):
    references = re.split(r'\n\s*\d*\s*', paragraph.strip())
    references = [ref for ref in references if ref.strip()]
    return references

def extract_title(reference):
    # Match patterns for different citation styles
    match = re.search(r'(?<!\.)\.\s+([^\.]+?)\.\s+\b(?:In:|IEEE|ACM|Proceedings of|Design Automation Conference)\b', reference)
    if not match:
        # Try another pattern
        match = re.search(r'(?<!\.)\.\s+([^\.]+?)\.\s+\d{4}', reference)
    if match:
        title = match.group(1).strip()
        return title
    return None

def extract_titles_from_paragraph(paragraph):
    references = extract_references(paragraph)
    titles = [extract_title(ref) for ref in references]
    return [title for title in titles if title]

@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        if request.method == 'POST':
            paragraph = request.form.get('paragraph')
            if paragraph:
                titles = extract_titles_from_paragraph(paragraph)
                if titles:
                    return render_template('index.html', titles=titles)
                else:
                    return render_template('index.html', error="No titles found in the provided paragraph.")
        return render_template('index.html')
    except Exception as e:
        logging.error(f"Error in index route: {e}")
        return render_template('index.html', error="An internal error occurred. Please try again later.")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
