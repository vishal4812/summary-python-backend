import re
from collections import Counter

from ..schemas import SummarizeRequest, SummarizeResponse

MODE_BULLET_LIMITS = {
    "short_bullets": 3,
    "long_bullets": 5,
    "paragraph": 4,
}
MIN_SENTENCE_LENGTH = 18


class HeuristicSummarizer:
    def summarize(self, payload: SummarizeRequest) -> SummarizeResponse:
        normalized_text = self._normalize(payload.text)
        sentences = self._split_sentences(normalized_text)
        bullet_points = self._select_key_points(sentences, payload.mode)
        summary = self._build_summary(bullet_points)
        detailed_summary = self._build_detailed_summary(
            bullet_points,
            payload.language,
        )

        return SummarizeResponse(
            summary=summary,
            bulletPoints=bullet_points,
            detailedSummary=detailed_summary,
            serviceMode="heuristic",
        )

    def _normalize(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def _split_sentences(self, text: str) -> list[str]:
        sentence_candidates = [
            part.strip(" -\t")
            for part in re.split(r"(?<=[.!?।])\s+|\n+", text)
        ]
        filtered = [
            candidate
            for candidate in sentence_candidates
            if len(candidate) >= MIN_SENTENCE_LENGTH
        ]

        if filtered:
            return filtered

        fallback_chunks = [
            part.strip(" -\t")
            for part in re.split(r"[;,\n]+", text)
            if len(part.strip()) >= MIN_SENTENCE_LENGTH
        ]
        return fallback_chunks or [text]

    def _select_key_points(self, sentences: list[str], mode: str) -> list[str]:
        limit = min(MODE_BULLET_LIMITS.get(mode, 3), len(sentences))
        token_frequencies = Counter(
            token
            for sentence in sentences
            for token in set(self._tokenize(sentence))
        )

        scored_sentences: list[tuple[float, int, str]] = []
        for index, sentence in enumerate(sentences):
            tokens = self._tokenize(sentence)
            lexical_score = sum(token_frequencies[token] for token in set(tokens))
            lexical_score /= max(len(tokens), 1)
            position_bonus = max(0.0, 0.4 - (index * 0.05))
            length_bonus = min(len(sentence) / 180, 0.35)
            total_score = lexical_score + position_bonus + length_bonus
            scored_sentences.append((total_score, index, sentence))

        top_sentences = sorted(
            scored_sentences,
            key=lambda item: (-item[0], item[1]),
        )[:limit]
        selected_indices = sorted(index for _, index, _ in top_sentences)

        return [self._clean_sentence(sentences[index]) for index in selected_indices]

    def _tokenize(self, sentence: str) -> list[str]:
        return [
            token.lower()
            for token in re.findall(r"\w+", sentence, flags=re.UNICODE)
            if len(token) > 2 and not token.isdigit()
        ]

    def _clean_sentence(self, sentence: str) -> str:
        cleaned = sentence.strip()
        if cleaned.endswith((".", "!", "?", "।")):
            return cleaned
        return f"{cleaned}."

    def _build_summary(self, bullet_points: list[str]) -> str:
        combined = " ".join(bullet_points[:2]).strip()
        if len(combined) <= 220:
            return combined
        return bullet_points[0]

    def _build_detailed_summary(
        self,
        bullet_points: list[str],
        language: str,
    ) -> str:
        heading = f"Auto-generated summary for the submitted {language} text."
        details = "\n".join(f"- {point}" for point in bullet_points)
        return f"{heading}\n\n{details}"
