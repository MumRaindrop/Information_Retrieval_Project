# Made with reference to sklearn and BeautifulSoup documentation and additional help from ChatGPT

import json
import sys
from sklearn.feature_extraction.text import TfidfVectorizer
from bs4 import BeautifulSoup

# File to load html from, should always be this
INPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else "../crawl_output.json"
# File to output the inverted index with tf idfs to 
OUTPUT_FILE = "index.json"

def main():
    # Open the file with the html
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        crawl_data = json.load(f)

    # Create a list for urls and their associated htmls
    urls = [d["url"] for d in crawl_data]
    html_docs = [d["html"] for d in crawl_data]
    clean_docs = []

    # Post processing on html to remove useless html tags
    def clean_html(html):
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(separator=" ")

    # Clean all the html documents and add them to the clean docs list
    for doc in html_docs:
        clean_docs.append(clean_html(doc))

    # Use scikit learn vectorizer to build a tfidf matrix excluding stop words
    vectorizer = TfidfVectorizer(
        stop_words="english",
        lowercase=True,
    )
    tfidf_matrix = vectorizer.fit_transform(clean_docs)

    # Build the list of terms from the tfidf matrix
    terms = vectorizer.vocabulary_
    inv_terms = {idx: term for term, idx in terms.items()}

    inverted_index = {}

    # Build the inverted index from the tfidf matrix
    for doc_id in range(tfidf_matrix.shape[0]):
        row = tfidf_matrix.getrow(doc_id)

        for term_index, tfidf_value in zip(row.indices, row.data):
            term = inv_terms[term_index]

            if term not in inverted_index:
                inverted_index[term] = []

            inverted_index[term].append((doc_id, float(tfidf_value)))
            # Stores the inverted index as term: (doc_id, tfidf) pairs

    # Output to be saved in the json file, urls in a list (position is doc_id) and the inverted index formatted as mentioned
    index = {
        "urls": urls,
        "inverted_index": inverted_index,
    }

    # Save the index to the json file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

if __name__ == "__main__":
    main()