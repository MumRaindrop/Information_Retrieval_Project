# Project assisted and partially generated using the assistance of LLM ChatGPT
from flask import Flask, request, Response
import csv
from indexer import SklearnIndexer
import os
from nltk.metrics import edit_distance

app = Flask(__name__)
INDEX_FILE = os.path.join(".", "inverted_index.json")
DOC_FOLDER = "."

indexer = SklearnIndexer(input_folder=DOC_FOLDER, output_file=INDEX_FILE)
VOCAB = set()

# run indexer if not existant
if not os.path.exists(INDEX_FILE):
    print("Inverted index not found, running indexer")
    indexer.run()
    VOCAB = set(indexer.vectorizer.get_feature_names_out())
else:
    print("Loading existing index")
    indexer.load_documents()
    indexer.build_tfidf()
    VOCAB = set(indexer.vectorizer.get_feature_names_out())

# spelling correction using edit distance
def spelling_check(query, vocab, max_distance=2):
    tokens = query.lower().split()
    suggestions = {}

    for t in tokens:
        if len(t) <= 2:
            continue

        closest_word = None
        closest_dist = 999

        for v in vocab:
            d = edit_distance(t, v)
            if d < closest_dist:
                closest_dist = d
                closest_word = v
            if closest_dist == 0:
                break

        if closest_dist <= max_distance and closest_word != t:
            suggestions[t] = closest_word

    return suggestions if suggestions else None

# format output
def format_output(query, data):
    lines = []
    lines.append(f"\nQuery: {query}")
    lines.append("Results:")
    for item in data.get("results", []):
        lines.append(f"  {item['document']} -> {item['score']}")

    suggestions = data.get("suggestions")
    if suggestions:
        lines.append("Suggestions:")
        for wrong, correct in suggestions.items():
            lines.append(f"  {wrong} -> {correct}")
    else:
        lines.append("Suggestions: None")

    return "\n".join(lines)


@app.route("/query", methods=["POST"])
def query_processor():
    if 'file' not in request.files:
        return Response("ERROR: No file provided", status=400)

    file = request.files['file']

    if not file.filename.endswith(".csv"):
        return Response("ERROR: Only CSV files allowed", status=400)

    decoded = file.read().decode("utf-8").splitlines()
    reader = csv.DictReader(decoded)

    if 'query' not in reader.fieldnames:
        return Response("ERROR: CSV must contain a 'query' column", status=400)

    queries = []
    for row in reader:
        text = row['query'].strip()
        if text:
            queries.append(text)

    if not queries:
        return Response("ERROR: No valid queries found", status=400)

    # build text output
    output_text = ""

    for q in queries:
        suggestion = spelling_check(q, VOCAB)
        raw_results = indexer.search(q, top_k=5)

        results = [
            {"document": doc, "score": float(score)}
            for doc, score in raw_results
        ]

        format_results = format_output(q, {"results": results, "suggestions": suggestion})
        output_text += format_results + "\n\n"

    return (output_text)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)