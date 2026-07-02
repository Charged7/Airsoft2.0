"""Scoring algorithm for quiz recommendations."""

from picker.models import Product

TYPE_PENALTIES = {
    "novice": {"GBBR": -3, "HPA": -3, "Spring": -2, "GBB": -1},
    "few_games": {"HPA": -1},
}

TYPE_BONUSES = {
    "realism": {"GBBR": 3, "GBB": 2},
    "compact": {},
}

ROLE_BONUSES = {
    "cqb": {"mp5-aeg": 3, "p90-aeg": 3, "m4-aeg": 1},
    "forest": {"ak-aeg": 2, "g36-aeg": 2},
    "field": {"ak-aeg": 2, "scar-aeg": 2, "m4-aeg": 1},
    "milsim": {"g36-aeg": 2, "scar-aeg": 2, "gbbr-m4": 2},
}

PRIORITY_WEIGHTS = {
    "reliability": {"reliability": 2.5, "repair_cost": 1.5, "beginner_friendly": 1.0},
    "realism": {"realism": 3.0, "status": 1.0, "drive": 1.0},
    "compact": {"comfort": 2.0, "cqb": 2.5},
    "status": {"status": 3.0, "drive": 1.5},
}

BEGINNER_SLUGS = {"m4-aeg", "ak-aeg"}
COMPACT_SLUGS = {"mp5-aeg", "p90-aeg", "gbb-pistol"}


def _base_score(product: Product, priority: str) -> float:
    scores = product.scores or {}
    weights = PRIORITY_WEIGHTS.get(priority, PRIORITY_WEIGHTS["reliability"])
    total = 0.0
    weight_sum = 0.0
    for key, weight in weights.items():
        total += scores.get(key, 0) * weight
        weight_sum += weight
    return total / weight_sum if weight_sum else 0.0


def score_products(products, answers: dict, top_n: int = 3) -> list[dict]:
    experience = answers.get("experience", "novice")
    play_style = answers.get("play_style", "field")
    priority = answers.get("priority", "reliability")
    budget = answers.get("budget", "medium")
    maintenance = answers.get("maintenance", "a_little")
    weight = answers.get("weight", "not_important")
    simple_start = answers.get("simple_start", "yes")

    results = []

    for product in products:
        score = _base_score(product, priority)

        for ptype, penalty in TYPE_PENALTIES.get(experience, {}).items():
            if product.type == ptype:
                score += penalty

        if experience == "novice" and product.slug in BEGINNER_SLUGS:
            score += 2

        for ptype, bonus in TYPE_BONUSES.get(priority, {}).items():
            if product.type == ptype:
                score += bonus

        score += ROLE_BONUSES.get(play_style, {}).get(product.slug, 0)

        if budget == "low" and product.budget_tier == "low":
            score += 2
        elif budget == "low" and product.budget_tier == "high":
            score -= 2
        elif budget == "high" and product.budget_tier == "high":
            score += 1

        if maintenance == "no":
            score += (product.scores or {}).get("reliability", 0) * 0.3
            score += (product.scores or {}).get("beginner_friendly", 0) * 0.3
        elif maintenance == "yes":
            score += (product.scores or {}).get("realism", 0) * 0.2

        if weight == "important" and product.slug in COMPACT_SLUGS:
            score += 2

        if simple_start == "yes" and product.slug in BEGINNER_SLUGS:
            score += 2
        elif simple_start == "no" and product.type in ("GBBR", "HPA"):
            score += 1.5

        results.append({"product": product, "score": round(score, 2)})

    results.sort(key=lambda item: item["score"], reverse=True)
    top = results[:top_n]
    max_score = top[0]["score"] if top else 1

    for item in top:
        item["match_percent"] = min(100, max(40, int((item["score"] / max(max_score, 1)) * 100)))

    return top
