from typing import List
import nltk
nltk.data.path.append('src/processing/nltk_data')
from nltk.tokenize import sent_tokenize
print("NLTK data paths:", nltk.data.path)

def fixed_size_chunk(text: str, size: int = 512) -> List[str]:
    return [text[i:i+size] for i in range(0, len(text), size)]

def sentence_chunk(text: str, max_sentences: int = 5) -> List[str]:
    print("NLTK data paths:", nltk.data.path)
    sentences = sent_tokenize(text)
    return [" ".join(sentences[i:i+max_sentences]) for i in range(0, len(sentences), max_sentences)]

def sliding_window_chunk(text: str, window_size: int = 512, stride: int = 256) -> List[str]:
    return [text[i:i+window_size] for i in range(0, len(text), stride)]
