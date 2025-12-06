# Done with reference to Flask documentation, Introduction to Information Retrieval (book), and additional help from ChatGPT

from flask import Flask, request, render_template, jsonify
import csv
import json
import io
import math
import subprocess
import os
from collections import defaultdict

app = Flask(__name__)

INDEX_FILE = "../index.json"
CRAWL_OUTPUT = "../crawl_output.json"

def load_index():
    # Load the index from the json file
    global urls, inverted_index
    if not os.path.exists(INDEX_FILE):
        # initialize index data structures
        urls = []
        inverted_index = {}
        return

    # Open and load the file into the data structures
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    urls = data["urls"]
    inverted_index = data["inverted_index"]

# call load_index at startup
load_index()

# tokenize function from past homework for use on text queries
def tokenize(text):
    clean = ""
    for c in text:
        if c.isalnum() or c.isspace():
            clean += c
    return clean.lower().split()

# Build a query vector based on given tokens
def build_query_vector(tokens):
    tf = defaultdict(int)
    # Create term frequencies for the terms in the query
    for t in tokens:
        tf[t] += 1

    qvec = {}
    for term, count in tf.items():
        if term in inverted_index:
            df = len(inverted_index[term]) # Document frequency, number of documents containing the term
            N = len(urls) # Total number of documents (Number of pages crawled)
            idf = math.log((N + 1) / (df + 1)) + 1 # Calculate the IDF
            qvec[term] = count * idf # Add the tfidf to the query vector for the term
    return qvec

# Get the cosine similarity scores for all of the documents (pages) crawled based on the query vector
def cosine_similarity_query(qvec):
    # Initialize data structures
    scores = defaultdict(float)
    doc_norms = defaultdict(float)

    #Get the numerator dot product between query vector and document vectors
    for term, qval in qvec.items():
        for doc_id, tfidf in inverted_index[term]:
            scores[doc_id] += qval * tfidf

    # Get the document normal for the denominator
    for term, postings in inverted_index.items():
        for doc_id, tfidf in postings:
            doc_norms[doc_id] += tfidf * tfidf

    # Get the query normal and finalize cosine similarity scores
    qnorm = math.sqrt(sum(v*v for v in qvec.values()))
    if qnorm == 0:
        return {}

    for doc_id in scores:
        scores[doc_id] /= (qnorm * math.sqrt(doc_norms[doc_id]))

    return scores

@app.route("/", methods=["GET"])
#Route for home page
def home():
    return render_template("index.html")

@app.route("/query_text", methods=["POST"])
# Gets query from textbox input from web ui
def query_text():
    # Get the query
    data = request.get_json()
    query = data.get("query", "").strip()

    # If no query return error
    if not query:
        return jsonify({"error": "Query text missing"}), 400

    # Tokenize the query and build and await the cosine similarity results
    tokens = tokenize(query)
    qvec = build_query_vector(tokens)
    sims = cosine_similarity_query(qvec)

    #Sort the results and get the top 5 relevant pages
    ranked = sorted(sims.items(), key=lambda x: x[1], reverse=True)[:5]

    # Output the results to the ui
    return jsonify({
        "query": query,
        "results": [
            {"url": urls[doc_id], "score": float(score)}
            for doc_id, score in ranked
        ]
    })

@app.route("/query", methods=["POST"])
# Query using an uploaded csv file
def query_csv():
    # Missing csv file
    if "file" not in request.files:
        return jsonify({"error": "CSV file missing"}), 400

    file = request.files["file"]
    rows = list(csv.reader(io.TextIOWrapper(file.stream, encoding="utf-8")))

    # csv not formatted correctly
    if len(rows) < 1 or len(rows[0]) < 1:
        return jsonify({"error": "CSV must contain a 'query' column"}), 400

    queries = [row[0] for row in rows]

    results = []

    # Do the same as in the text query route but for each of the queries in the csv file
    for q in queries:
        tokens = tokenize(q)
        qvec = build_query_vector(tokens)
        sims = cosine_similarity_query(qvec)
        ranked = sorted(sims.items(), key=lambda x: x[1], reverse=True)[:5]

        results.append({
            "query": q,
            "results": [
                {"url": urls[doc_id], "score": float(score)}
                for doc_id, score in ranked
            ]
        })

    return jsonify(results)

@app.route("/crawl", methods=["POST"])
# Start a crawl using the spider from the ui
def crawl():
    data = request.get_json()
    #Get the necessary parameters for the crawl
    seed = data.get("seed")
    max_pages = data.get("max_pages", 10)
    max_depth = data.get("max_depth", 2)

    #If there is no url
    if not seed:
        return jsonify({"error": "seed URL required"}), 400

    # Set the project directory
    SCRAPY_PROJECT_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "crawler")
    )

    # Run the crawl using this command
    cmd = [
        "scrapy", "crawl", "spider",
        "-a", f"seed_url={seed}",
        "-a", f"max_pages={max_pages}",
        "-a", f"max_depth={max_depth}",
        "-O", "crawl_output.json"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=SCRAPY_PROJECT_DIR  # 👈 IMPORTANT
    )

    # Return verification of the crawl
    return jsonify({
        "status": "crawl completed",
        "stdout": result.stdout,
        "stderr": result.stderr
    })

@app.route("/build_index", methods=["POST"])
# Build the index using the build_index file from the ui
def build_index():
    # Get the locations of relevant files, crawl_output, build_index, and index
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    INDEX_FILE = os.path.join(PROJECT_ROOT, "index.json")
    CRAWL_OUTPUT = os.path.join(PROJECT_ROOT, "crawler", "crawl_output.json")
    BUILD_INDEX_SCRIPT = os.path.join(PROJECT_ROOT, "indexer", "build_index.py")

    # Run the build_index file using this command
    cmd = [
        "python",
        BUILD_INDEX_SCRIPT,
        CRAWL_OUTPUT
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )

    # Reload the index for use after rebuilding
    global urls, inverted_index
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        urls = data["urls"]
        inverted_index = data["inverted_index"]
    else:
        urls = []
        inverted_index = {}

    # Return that the index was built
    return jsonify({
        "status": "index rebuilt and reloaded",
        "stdout": result.stdout,
        "stderr": result.stderr
    })

if __name__ == "__main__":
    app.run(debug=True)