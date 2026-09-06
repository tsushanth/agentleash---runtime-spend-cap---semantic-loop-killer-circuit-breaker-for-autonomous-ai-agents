"""Semantic re-planning loop detection.

Catches agents that keep re-planning the "same" step in different words
(e.g. "retry fetching the API" vs "let me try the API call again") using
difflib.SequenceMatcher combined with word-overlap (Jaccard) similarity —
no embeddings, API key, or network access required.
"""

import difflib
import re

_WORD_RE = re.compile(r"[a-z0-9]+")


def _normalize(text):
    return text.strip().lower()


def _words(text):
    return set(_WORD_RE.findall(text.lower()))


def similarity_score(a, b):
    """Blend of character-sequence similarity and word-overlap similarity, in [0, 1]."""
    seq_ratio = difflib.SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()

    wa, wb = _words(a), _words(b)
    jaccard = len(wa & wb) / len(wa | wb) if (wa or wb) else 0.0

    return (seq_ratio + jaccard) / 2


class LoopDetector:
    """Flags a run as looping once N consecutive steps are semantically
    similar to a recent prior step, rather than requiring an exact repeat.
    """

    def __init__(self, similarity_threshold=0.6, max_consecutive_similar=3, window=5):
        self.similarity_threshold = similarity_threshold
        self.max_consecutive_similar = max_consecutive_similar
        self.window = window
        self._history = []
        self._consecutive = 0
        self.last_similarity = 0.0

    def observe(self, step_text):
        """Record a new step and return True if the loop threshold has just been hit."""
        best = 0.0
        for prev in self._history[-self.window:]:
            best = max(best, similarity_score(prev, step_text))
        self.last_similarity = best

        if best >= self.similarity_threshold:
            self._consecutive += 1
        else:
            self._consecutive = 0

        self._history.append(step_text)

        return self._consecutive >= self.max_consecutive_similar
