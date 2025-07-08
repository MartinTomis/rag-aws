This needs to be loaded first.

import nltk

try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")





4. Use __name__ == "__main__" or FastAPI startup event
If you have init code (like init_schema()), do not run it directly at import-time — do this:

python
Copy
Edit
def init():
    init_schema()

if __name__ == "__main__":
    init()
Or in FastAPI:

python
Copy
Edit
@app.on_event("startup")
def on_startup():
    init_schema()