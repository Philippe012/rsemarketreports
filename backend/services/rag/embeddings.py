from __future__ import annotations

import hashlib
import logging
import math
import os
from typing import List, Optional, Tuple

from services.chat.text_match import significant_words, tokenize
from openai import OpenAI

logger = logging.getLogger(__name__)

LOCAL_MODEL_NAME = 'local-hash-v1'
LOCAL_DIMENSIONS = 512
OPENAI_DEFAULT_MODEL = 'text-embedding-3-small'
OPENAI_BATCH_SIZE = 100


def _openai_key() -> str:
    return os.environ.get('OPENAI_API_KEY', '').strip()


def using_openai() -> bool:
    return bool(_openai_key()) and os.environ.get('RAG_EMBEDDINGS', '').strip().lower() != 'local'


def embedding_model_name() -> str:
    if using_openai():
        return 'openai:' + os.environ.get('RAG_EMBEDDING_MODEL', OPENAI_DEFAULT_MODEL)
    return LOCAL_MODEL_NAME


# local embedder

def _bucket(feature: str) -> tuple:
    digest = hashlib.md5(feature.encode('utf-8')).digest()
    index = int.from_bytes(digest[:4], 'little') % LOCAL_DIMENSIONS
    sign = 1.0 if digest[4] & 1 else -1.0
    return index, sign


def _local_embed(text: str) -> List[float]:
    vector = [0.0] * LOCAL_DIMENSIONS
    keep = significant_words(text)
    words = [w for w in tokenize(text) if w in keep]
    features = words + [f'{a} {b}' for a, b in zip(words, words[1:])]
    
    for feature in features:
        index, sign = _bucket(feature)
        vector[index] += sign
    norm = math.sqrt(sum(v * v for v in vector))
    return [v / norm for v in vector] if norm else vector


# OpenAI embedder

def _openai_embed_many(texts: List[str], model: Optional[str] = None) -> List[List[float]]:

    client = OpenAI(api_key=_openai_key())
    model = model or os.environ.get('RAG_EMBEDDING_MODEL', OPENAI_DEFAULT_MODEL)
    vectors: List[List[float]] = []
    
    for start in range(0, len(texts), OPENAI_BATCH_SIZE):
        batch = [t.replace('\n', ' ') or ' ' for t in texts[start:start + OPENAI_BATCH_SIZE]]
        response = client.embeddings.create(model=model, input=batch)
        vectors.extend(item.embedding for item in sorted(response.data, key=lambda d: d.index))
    return vectors


# public interface

def embed_texts(texts: List[str]) -> Tuple[str, List[List[float]]]:
    if not texts:
        return embedding_model_name(), []
    if using_openai():
        try:
            return embedding_model_name(), _openai_embed_many(texts)
        except Exception:
            logger.exception('OpenAI embeddings failed; falling back to %s', LOCAL_MODEL_NAME)
    return LOCAL_MODEL_NAME, [_local_embed(t) for t in texts]


def embed_text(text: str) -> List[float]:
    return embed_texts([text])[1][0]


def embed_question(question: str, model_name: Optional[str] = None) -> Optional[List[float]]:
    """Embeds a question with a specific model so it can be compared with
    chunks built by that model. Returns None if that model is unavailable."""
    model_name = model_name or embedding_model_name()
    if model_name == LOCAL_MODEL_NAME:
        return _local_embed(question)
    if not model_name.startswith('openai:') or not _openai_key():
        return None
    try:
        return _openai_embed_many([question], model=model_name.split(':', 1)[1])[0]
    except Exception:
        logger.exception('OpenAI question embedding failed')
        return None
