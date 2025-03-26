from fastapi import FastAPI, HTTPException
from elasticsearch import Elasticsearch
import requests
from bs4 import BeautifulSoup

app = FastAPI()

# Connecting to Elasticsearch (inside the same Docker network)
es = Elasticsearch(["http://elasticsearch:9200"])

INDEX_NAME = "documents"
WIKI_URL = "https://en.wikipedia.org/wiki/India"

def fetch_wikipedia_paragraphs():
    """Scrapes the first 4 paragraphs from Wikipedia."""
    response = requests.get(WIKI_URL)
    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    paragraphs = soup.find_all("p")  # Get all paragraphs

    # Extracting text from the first 4 valid paragraphs 
    valid_paragraphs = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
    return valid_paragraphs[:4]  # Take only the first 4

@app.on_event("startup")
async def setup_index():
    """Create index if it doesn't exist and insert Wikipedia paragraphs."""
    if not es.indices.exists(index=INDEX_NAME):
        es.indices.create(
            index=INDEX_NAME,
            body={
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "text": {"type": "text"}
                    }
                }
            }
        )
        # Fetching and inserting Wikipedia data
        wiki_paragraphs = fetch_wikipedia_paragraphs()
        for i, text in enumerate(wiki_paragraphs):
            es.index(index=INDEX_NAME, id=str(i + 1), document={"id": str(i + 1), "text": text})

@app.post("/insert")
async def insert_document(data: dict):
    """Insert a document into Elasticsearch."""
    if "text" not in data:
        raise HTTPException(status_code=400, detail="Missing 'text' field in request")
    
    doc_id = str(hash(data["text"]))
    es.index(index=INDEX_NAME, id=doc_id, document={"id": doc_id, "text": data["text"]})
    
    return {"message": "Document inserted successfully", "document_id": doc_id}

@app.get("/search")
async def search_document(query: str):
    """to perform a match search in Elasticsearch."""
    response = es.search(
        index=INDEX_NAME,
        body={"query": {"match": {"text": query}}}
    )
    results = [{"id": hit["_id"], "text": hit["_source"]["text"]} for hit in response["hits"]["hits"]]
    
    if not results:
        return {"message": "No matching documents found"}
    
    return {"results": results}
