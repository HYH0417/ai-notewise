import hashlib
import re

import numpy as np


class EmbeddingService:
    """Small local hashing embedding service for instant skill search."""

    def __init__(self):
        self.embedding_dim = 384

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"[a-zA-Z0-9_]+|[\u4e00-\u9fff]", text.lower())

    def _index_for_token(self, token: str) -> int:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        return int.from_bytes(digest, "big") % self.embedding_dim

    def encode(self, text: str) -> np.ndarray:
        tokens = self._tokenize(text)
        embedding = np.zeros(self.embedding_dim)

        for token in tokens:
            embedding[self._index_for_token(token)] += 1.0

        norm = np.linalg.norm(embedding)
        if norm:
            embedding = embedding / norm
        return embedding

    def encode_batch(self, texts: list[str]) -> np.ndarray:
        return np.array([self.encode(text) for text in texts])
