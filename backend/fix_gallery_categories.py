"""Fix gallery.json categories based on paper titles and abstracts."""
import json
import re
from pathlib import Path

GALLERY_PATH = Path("app/static/gallery/gallery.json")

# Keywords that map to categories
CATEGORY_RULES = [
    ("table", ["benchmark", "dataset", "comparison", "evaluat", "survey", "review", "leaderboard", "metric", "performance"]),
    ("architecture", ["architecture", "network", "backbone", "transformer", "cnn", "mlp", "diffusion model", "generative model", "encoder", "decoder", "attention mechanism", "multi-modal", "multimodal", "foundation model"]),
    ("framework", ["framework", "platform", "system", "toolkit", "library", "toolbox", "suite", "pipeline", "workflow"]),
    ("concept_map", ["representation", "embedding", "feature", "latent", "knowledge graph", "graph", "topology", "structure", "hierarchy"]),
    ("comparison", ["vs", "versus", "compare", "ablation", "baseline", "state-of-the-art", "sota", "outperform", "superior"]),
    ("freeform", ["tutorial", "overview", "introduction", "primer", "guide"]),
]

# Default fallback
def classify_item(item: dict) -> str:
    text = f"{item.get('title', '')} {item.get('abstract', '')} {' '.join(item.get('tags', []))}".lower()

    scores = {}
    for cat, keywords in CATEGORY_RULES:
        score = 0
        for kw in keywords:
            if kw in text:
                score += 1
        scores[cat] = score

    # If no clear match, check for specific patterns
    if scores["table"] >= 2:
        return "table"
    if scores["architecture"] >= 2:
        return "architecture"
    if scores["framework"] >= 2:
        return "framework"
    if scores["concept_map"] >= 2:
        return "concept_map"
    if scores["comparison"] >= 2:
        return "comparison"
    if scores["freeform"] >= 1:
        return "freeform"

    # Heuristic: if title contains "benchmark" or "dataset"
    title_lower = item.get('title', '').lower()
    if any(w in title_lower for w in ['benchmark', 'dataset', 'evaluation', 'survey']):
        return 'table'
    if any(w in title_lower for w in ['architecture', 'network', 'model']):
        return 'architecture'
    if any(w in title_lower for w in ['framework', 'system', 'platform']):
        return 'framework'

    # Default to pipeline for method/workflow papers
    return "pipeline"


def main():
    with open(GALLERY_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    categories = {}
    for item in data:
        new_cat = classify_item(item)
        item['category'] = new_cat
        categories[new_cat] = categories.get(new_cat, 0) + 1

    with open(GALLERY_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Updated {len(data)} gallery items. Category distribution:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")


if __name__ == '__main__':
    main()
