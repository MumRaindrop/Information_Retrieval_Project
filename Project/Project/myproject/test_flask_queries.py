import requests

csv_file_path = "queries.csv" 

url = "http://127.0.0.1:5000/query"

with open(csv_file_path, "rb") as f:
    files = {"file": f}
    try:
        response = requests.post(url, files=files)
        response.raise_for_status()  
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    else:
        try:
            results = response.json()
            print("Query Results:")
            for query, hits in results.items():
                print(f"\nQuery: {query}")
                for doc_id, score in hits:
                    print(f"  {doc_id} -> {score:.4f}")
        except ValueError:
            print("Failed to parse JSON response:")
            print(response.text)