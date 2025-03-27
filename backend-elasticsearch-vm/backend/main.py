import time
from fastapi import FastAPI, HTTPException
from elasticsearch import Elasticsearch
import requests
from bs4 import BeautifulSoup

app = FastAPI()

# Retry connecting to Elasticsearch
ES_HOST = "http://elasticsearch:9200"
es = None

for _ in range(10):  # Retry for 10 attempts
    try:
        es = Elasticsearch([ES_HOST])
        if es.ping():
            print("Connected to Elasticsearch")
            break
    except Exception as e:
        print(f"Waiting for Elasticsearch... {e}")
    time.sleep(5)  # Wait 5 seconds before retrying

if not es or not es.ping():
    raise Exception("Failed to connect to Elasticsearch")

INDEX_NAME = "documents"
WIKI_URL = "https://en.wikipedia.org/wiki/India"

def fetch_wikipedia_paragraphs():
    response = requests.get(WIKI_URL)
    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    paragraphs = soup.find_all("p")
    valid_paragraphs = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
    return valid_paragraphs[:4]

@app.on_event("startup")
async def setup_index():
    if not es.indices.exists(index=INDEX_NAME):
        es.indices.create(
            index=INDEX_NAME,
            body={"mappings": {"properties": {"id": {"type": "keyword"}, "text": {"type": "text"}}}}
        )
        wiki_paragraphs = fetch_wikipedia_paragraphs()
        for i, text in enumerate(wiki_paragraphs):
            es.index(index=INDEX_NAME, id=str(i + 1), document={"id": str(i + 1), "text": text})

@app.post("/insert")
async def insert_document(data: dict):
    if "text" not in data:
        raise HTTPException(status_code=400, detail="Missing 'text' field in request")

    doc_id = str(hash(data["text"]))
    es.index(index=INDEX_NAME, id=doc_id, document={"id": doc_id, "text": data["text"]})

    return {"message": "Document inserted successfully", "document_id": doc_id}

@app.get("/search")
async def search_document(query: str):
    response = es.search(index=INDEX_NAME, body={"query": {"match": {"text": query}}})
    results = [{"id": hit["_id"], "text": hit["_source"]["text"]} for hit in response["hits"]["hits"]]

    return {"results": results} if results else {"message": "No matching documents found"}
