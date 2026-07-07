"""
Scoring algorithm for quiz recommendations.

scores — шкала 1–10.
Ваги —  цілі числа 1, 2, 3:
1 — звичайна важливість;
2 — висока;
3 — ключова.
"""

from picker.models import Product


EXPERIENCE_TYPE_MODIFIERS = {
    "novice": {
        "AEG": 3,
        "GBBR": -3,
        "GBB": -2,
        "HPA": -3,
        "Spring": -1
    },
    "few_games": {
        "AEG": 2,
        "GBBR": -2,
        "GBB": -1,
        "HPA": -2
    },
    "experienced": {
        "AEG": 2,
        "GBBR": 2,
        "GBB": 1,
        "HPA": 2
    },
}

PRIORITY_TYPE_MODIFIERS = {
    "realism": {
        "AEG": 0,
        "GBBR": 3,
        "GBB": 3,
        "HPA": 1,
        "Spring": 1
    },
    "ergonomics": {},
    "reliability": {
        "AEG": 3,
        "GBBR": -1,
        "GBB": -1,
        "HPA": 1,
        "Spring": 0
    },
    "status": {
        "AEG": 0,
        "GBBR": 3,
        "GBB": 2,
        "HPA": 2,
        "Spring": 2
    },
}

PLAY_STYLE_BONUS_POINTS = 2
PLAY_ROLE_BONUS_POINTS = 1
BEGINNER_PLATFORM_BONUS_POINTS = 2
MIN_SCORE_VALUE = 1
MAX_SCORE_VALUE = 10
MAX_SCORE = 40
MIN_MATCH_PERCENT = 0
MAX_MATCH_PERCENT = 100

PRIORITY_WEIGHTS = {
    "reliability": {
        "reliability": 2.5,
        "repair_cost": 1.5,
        "beginner_friendly": 1.0
    },
    "realism": {
        "drive": 2.0,
        "status": 1.0
    },
    "ergonomics": {
        "comfort": 2.0,
        "weight": 2.0,
        "cqb": 1.0
    },
    "status": {
        "status": 3.0,
        "drive": 1.5
    },
}

BEGINNER_PLATFORM_SLUGS = {
    "m4-aeg",
    "ak-aeg"
}

PLAY_ROLE_TAGS = {
    "assault",
    "sniper",
    "support",
}

PRODUCT_GOAL_TYPE_MODIFIERS = {
    "primary": {
        "AEG": 1.5,
        "GBBR": 1,
        "HPA": 1,
        "Spring": -1,
        "GBB": -3,
    },
    "sidearm": {
        "GBB": 4,
        "AEG": -2,
        "GBBR": -3,
        "HPA": -3,
        "Spring": -2,
    },
}

# TODO розібратись чи не перекриває ролі гравця
#  Найбільший ризик зараз — подвійне нарахування схожих сенсів.
#  Наприклад:
#  product_goal=sniper_platform;
#  play_role=sniper.
PRODUCT_GOAL_ROLE_MODIFIERS = {
    "sniper_platform": "sniper",
    "support_platform": "support",
}

NEUTRAL_PRODUCT_GOALS = {
    "any",
}

WEATHER_TYPE_MODIFIERS = {
    "warm": {
        "GBBR": 1,
        "GBB": 1,
    },
    "cold": {
        "AEG": 1.5,
        "HPA": 1,
        "Spring": 0.5,
        "GBBR": -4,
        "GBB": -3,
    },
    "mixed": {
        "AEG": 0.5,
        "HPA": 0.5,
        "GBBR": -1,
        "GBB": -1,
    },
}

EXTRA_GEAR_TYPE_MODIFIERS = {
    "minimal": {
        "AEG": 1,
        "Spring": 0.5,
        "GBB": -1,
        "GBBR": -2,
        "HPA": -3,
    },
    "some": {},
    "ready": {
        "GBB": 0.5,
        "GBBR": 1.5,
        "HPA": 2,
    },
}

TUNING_UPGRADE_POTENTIAL_FACTORS = {
    "no": 0.0,
    "basic": 0.15,
    "yes": 0.35,
}

class MissingScoresError(ValueError):
    """Піднімається, коли у продукту не заповнені scores."""

REQUIRED_SCORE_KEYS = {
    "reliability",
    "repair_cost",
    "beginner_friendly",
    "status",
    "drive",
    "comfort",
    "weight",
    "cqb",
    "upgrade_potential",
}

def _validate_scores(product: Product) -> dict:
    """
    Перевіряє, що продукт має всі числові поля scores, потрібні для scoring.

    Піднімає MissingScoresError, якщо дані каталогу неповні, нечислові
    або виходять за допустимий діапазон scores 1..10.
    """
    scores = product.scores
    if not scores:
        raise MissingScoresError(f"Продукт '{product.slug}' (id={product.id}) має порожнє поле scores.")

    missing_keys = REQUIRED_SCORE_KEYS - scores.keys()
    if missing_keys:
        raise MissingScoresError(
            f"Продукт '{product.slug}' (id={product.id}) не має заповнених полів scores: {sorted(missing_keys)}."
        )

    for key in REQUIRED_SCORE_KEYS:
        value = scores[key]

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise MissingScoresError(
                f"Продукт '{product.slug}' (id={product.id}) має нечислове поле scores['{key}']: {value!r}."
            )

        if not MIN_SCORE_VALUE <= value <= MAX_SCORE_VALUE:
            raise MissingScoresError(
                f"Продукт '{product.slug}' (id={product.id}) має scores['{key}']={value}, "
                f"очікується значення від {MIN_SCORE_VALUE} до {MAX_SCORE_VALUE}."
            )

    return scores


def _base_score(scores: dict, priority: str) -> float:
    """
    Рахує зважену середню оцінку для вибраного користувачем priority.

    Priority має бути провалідований до scoring; невідомі значення піднімають
    ValueError замість тихого fallback на іншу модель обрахунку.
    """
    if priority not in PRIORITY_WEIGHTS:
        raise ValueError(f"Unknown priority: {priority!r}")

    weights = PRIORITY_WEIGHTS[priority]
    total = 0.0
    weight_sum = 0.0
    for key, weight in weights.items():
        total += scores.get(key, 0) * weight
        weight_sum += weight
    return total / weight_sum


def _match_percent(score: float) -> int:
    """
    Перетворює абсолютний score у match percentage з обмеженням діапазону.

    MAX_SCORE є бізнес-стелею для майже ідеальної рекомендації, тому
    перший товар не отримує 100% автоматично.
    """
    percent = int((score / MAX_SCORE) * 100)
    return min(
        MAX_MATCH_PERCENT,
        max(MIN_MATCH_PERCENT, percent),
    )


def _matches_play_style(product: Product, play_style: str) -> bool:
    return play_style in (product.roles or [])


def _matches_play_role(product: Product, play_role: str) -> bool:
    return (
        play_role in PLAY_ROLE_TAGS
        and play_role in (product.roles or [])
    )


def _product_goal_modifier(product: Product, product_goal: str) -> float:
    """
    Повертає модифікатор score для цілі, з якою користувач шукає продукт.

    Цілі primary і sidearm звіряються за типом продукту. Цілі
    sniper_platform і support_platform звіряються за семантичними тегами в
    product.roles. Нейтральні цілі явно повертають 0.
    """
    if product_goal in PRODUCT_GOAL_TYPE_MODIFIERS:
        return PRODUCT_GOAL_TYPE_MODIFIERS[product_goal][product.type]

    if product_goal in PRODUCT_GOAL_ROLE_MODIFIERS:
        target_role = PRODUCT_GOAL_ROLE_MODIFIERS[product_goal]
        roles = product.roles or []
        return 3 if target_role in roles else -1.5

    if product_goal in NEUTRAL_PRODUCT_GOALS:
        return 0

    raise KeyError(f"Unsupported product_goal: {product_goal}")


def _tuning_modifier(scores: dict, tuning: str) -> float:
    """
    Рахує бонус за готовність користувача доробляти платформу після покупки.

    upgrade_potential працює як експертна оцінка потенціалу апгрейду: чим
    вища готовність до тюнінгу, тим сильніше цей score впливає на результат.
    """
    return scores["upgrade_potential"] * TUNING_UPGRADE_POTENTIAL_FACTORS[tuning]


def score_products(products, answers: dict, top_n: int = 3) -> list[dict]:
    """
    Ранжує продукти за валідованими відповідями quiz і повертає найкращі збіги.

    Очікує, що обов'язкові відповіді quiz провалідовані serializer-ом до
    виклику цієї функції. Дані scores перевіряються для кожного продукту перед
    застосуванням модифікаторів priority, experience, role, tuning, budget,
    weather, gear і simple_start.
    """
    experience = answers["experience"]
    product_goal = answers["product_goal"]
    play_style = answers["play_style"]
    play_role = answers["play_role"]
    priority = answers["priority"]
    budget = answers["budget"]
    maintenance = answers["maintenance"]
    tuning = answers["tuning"]
    weight_importance = answers["weight"]
    weather = answers["weather"]
    extra_gear = answers["extra_gear"]
    simple_start = answers["simple_start"]

    results = []

    for product in products:
        scores = _validate_scores(product)
        score = _base_score(scores, priority)

        for ptype, penalty in EXPERIENCE_TYPE_MODIFIERS[experience].items():
            if product.type == ptype:
                score += penalty

        for ptype, bonus in PRIORITY_TYPE_MODIFIERS[priority].items():
            if product.type == ptype:
                score += bonus

        if _matches_play_style(product, play_style):
            score += PLAY_STYLE_BONUS_POINTS

        if play_role and _matches_play_role(product, play_role):
            score += PLAY_ROLE_BONUS_POINTS

        score += _product_goal_modifier(product, product_goal)

        if budget == "low" and product.budget_tier == "low":
            score += 2
        elif budget == "low" and product.budget_tier == "high":
            score -= 2
        elif budget == "high" and product.budget_tier == "high":
            score += 1

        if maintenance == "no":
            score += scores["reliability"] * 0.3
            score += scores["beginner_friendly"] * 0.3
        elif maintenance == "yes":
            score += scores["drive"] * 0.2

        score += _tuning_modifier(scores, tuning)

        if weight_importance == "important":
            score += scores["weight"] * 0.3

        for ptype, modifier in WEATHER_TYPE_MODIFIERS[weather].items():
            if product.type == ptype:
                score += modifier

        for ptype, modifier in EXTRA_GEAR_TYPE_MODIFIERS[extra_gear].items():
            if product.type == ptype:
                score += modifier

        if simple_start == "yes" and product.slug in BEGINNER_PLATFORM_SLUGS:
            score += BEGINNER_PLATFORM_BONUS_POINTS
        elif simple_start == "no" and product.type in ("GBBR", "HPA"):
            score += 1.5

        results.append({"product": product, "score": round(score, 2)})

    results.sort(key=lambda item: item["score"], reverse=True)
    top = results[:top_n]

    for item in top:
        item["match_percent"] = _match_percent(item["score"])

    return top
