from indexer import SklearnIndexer

if __name__ == "__main__":
    indexer = SklearnIndexer(input_folder=".", output_file="./inverted_index.json")
    indexer.run()

    # Try a test query afterwards:
    print("\nSearch Results:")
    print(indexer.search("test query", top_k=5))