from fastapi import FastAPI, Form
import requests
from fastapi.responses import HTMLResponse

app = FastAPI()

# Backend API URL 
BACKEND_URL = "http://34.47.255.91:9567"

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Elasticsearch Query Interface</title>
</head>
<body>
    <h2>Search Elasticsearch</h2>
    <form method="post">
        <input type="text" name="query" placeholder="Enter search query">
        <button type="submit" formaction="/get">Get</button>
        <button type="submit" formaction="/insert">Insert</button>
    </form>
    <h3>Response:</h3>
    <pre id="output">{output}</pre>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_PAGE.format(output="")

@app.post("/get", response_class=HTMLResponse)
async def get_query(query: str = Form(...)):
    response = requests.get(f"{BACKEND_URL}/search", params={"query": query})
    return HTML_PAGE.format(output=response.text)

@app.post("/insert", response_class=HTMLResponse)
async def insert_query(query: str = Form(...)):
    response = requests.post(f"{BACKEND_URL}/insert", json={"text": query})
    return HTML_PAGE.format(output=response.text)
