from typing import List
import nltk
import pickle
import os
from nltk.tokenize.punkt import PunktSentenceTokenizer
nltk.data.path.append('src/processing/nltk_data')
from nltk.tokenize import sent_tokenize


print("NLTK data paths:", nltk.data.path)

def fixed_size_chunk(text: str, size: int = 512) -> List[str]:
    return [text[i:i+size] for i in range(0, len(text), size)]

tokenizer_path = os.path.join("src", "processing", "nltk_data", "tokenizers", "punkt", "english.pickle")

with open(tokenizer_path, "rb") as f:
    tokenizer = pickle.load(f) 

def sentence_chunk(text: str, max_sentences: int = 5):
    sentences = tokenizer.tokenize(text)
    return [
        " ".join(sentences[i:i + max_sentences])
        for i in range(0, len(sentences), max_sentences)
    ]

def sliding_window_chunk(text: str, window_size: int = 512, stride: int = 256) -> List[str]:
    return [text[i:i+window_size] for i in range(0, len(text), stride)]
