from typing import List
import nltk
from nltk.tokenize import sent_tokenize

def fixed_size_chunk(text: str, size: int = 512) -> List[str]:
    return [text[i:i+size] for i in range(0, len(text), size)]

def sentence_chunk(text: str, max_sentences: int = 5) -> List[str]:
    sentences = sent_tokenize(text)
    return [" ".join(sentences[i:i+max_sentences]) for i in range(0, len(sentences), max_sentences)]

def sliding_window_chunk(text: str, window_size: int = 512, stride: int = 256) -> List[str]:
    return [text[i:i+window_size] for i in range(0, len(text), stride)]
