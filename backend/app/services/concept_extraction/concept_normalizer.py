import logging

from app.llm.clients import BaseLLMClient
from app.llm.prompts.loader import load_prompt

logger = logging.getLogger(__name__)


class ConceptNormalizer:
    def __init__(self, llm: BaseLLMClient):
        self.llm = llm

    async def normalize(self, raw_concepts: list[dict]) -> list[dict]:
        """Two-pass deduplication: deterministic merge, then LLM-assisted dedup."""
        merged = self._deterministic_merge(raw_concepts)
        deduped = await self._llm_dedup(merged)
        return deduped

    def _deterministic_merge(self, concepts: list[dict]) -> list[dict]:
        """Merge concepts with identical normalized names."""
        by_name: dict[str, dict] = {}

        for c in concepts:
            key = c["name"].strip().lower()
            if key in by_name:
                existing = by_name[key]
                existing["source_chunk_ids"] = list(
                    set(existing.get("source_chunk_ids", []) + c.get("source_chunk_ids", []))
                )
                existing["prerequisite_names"] = list(
                    set(existing.get("prerequisite_names", []) + c.get("prerequisite_names", []))
                )
                existing["common_confusions"] = list(
                    set(existing.get("common_confusions", []) + c.get("common_confusions", []))
                )
                importance_rank = {"core": 3, "supporting": 2, "optional": 1}
                if importance_rank.get(c.get("importance"), 0) > importance_rank.get(
                    existing.get("importance"), 0
                ):
                    existing["importance"] = c["importance"]
                existing["difficulty"] = max(
                    existing.get("difficulty", 1), c.get("difficulty", 1)
                )
            else:
                by_name[key] = {**c, "normalized_name": key}

        return list(by_name.values())

    async def _llm_dedup(self, concepts: list[dict]) -> list[dict]:
        """Use LLM to find near-duplicates among concept names."""
        if len(concepts) <= 2:
            return concepts

        names = [c["name"] for c in concepts]
        prompt = load_prompt("concept_dedup", concept_names="\n".join(f"- {n}" for n in names))

        try:
            data = await self.llm.generate_json(prompt, task="concept_dedup")
        except Exception:
            logger.warning("LLM dedup failed, skipping near-duplicate merge")
            return concepts

        groups = data.get("groups", [])
        if not groups:
            return concepts

        name_to_concept = {c["name"].strip().lower(): c for c in concepts}
        to_remove: set[str] = set()

        for group in groups:
            canonical = group.get("canonical", "").strip().lower()
            duplicates = [d.strip().lower() for d in group.get("duplicates", [])]

            if canonical not in name_to_concept:
                continue

            target = name_to_concept[canonical]
            for dup_name in duplicates:
                if dup_name in name_to_concept and dup_name != canonical:
                    dup = name_to_concept[dup_name]
                    target["source_chunk_ids"] = list(
                        set(target.get("source_chunk_ids", []) + dup.get("source_chunk_ids", []))
                    )
                    target["prerequisite_names"] = list(
                        set(target.get("prerequisite_names", []) + dup.get("prerequisite_names", []))
                    )
                    target["common_confusions"] = list(
                        set(target.get("common_confusions", []) + dup.get("common_confusions", []))
                    )
                    to_remove.add(dup_name)

        return [c for c in concepts if c["name"].strip().lower() not in to_remove]
