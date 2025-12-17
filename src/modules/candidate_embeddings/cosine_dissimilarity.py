import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def cosine_dissimilarity_matrix(embeddings):
    similarity = cosine_similarity(embeddings)
    dissimilarity = 1 - similarity
    dissimilarity[dissimilarity < 0] = 0.0   # numerical stability
    return dissimilarity
