from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from picker.data.product_catalog import PRODUCTS
from picker.data.quiz_questions import QUIZ_QUESTIONS
from picker.models import Product, QuizSubmission
from picker.services.scoring import (
    BEGINNER_PLATFORM_BONUS_POINTS,
    MAX_SCORE,
    PLAY_ROLE_BONUS_POINTS,
    score_products,
)


FULL_SCORES = {
    "reliability": 8,
    "repair_cost": 8,
    "beginner_friendly": 8,
    "status": 6,
    "drive": 6,
    "comfort": 8,
    "weight": 8,
    "cqb": 8,
    "upgrade_potential": 7,
}


def create_product(slug, **overrides):
    data = {
        "slug": slug,
        "name": slug.upper(),
        "type": "AEG",
        "roles": ["field"],
        "scores": FULL_SCORES,
        "summary": f"{slug} summary",
        "description": "",
        "budget_tier": "medium",
    }
    data.update(overrides)

    return Product.objects.create(**data)


def quiz_answers(**overrides):
    data = {
        "experience": "experienced",
        "product_goal": "any",
        "play_style": "field",
        "play_role": "assault",
        "priority": "reliability",
        "budget": "medium",
        "maintenance": "a_little",
        "tuning": "no",
        "weight": "not_important",
        "weather": "mixed",
        "extra_gear": "some",
        "simple_start": "no",
    }
    data.update(overrides)

    return data


def catalog_scores(slug):
    products_by_slug = {
        product["slug"]: product
        for product in PRODUCTS
    }

    return products_by_slug[slug]["scores"]


def catalog_weight(slug):
    return catalog_scores(slug)["weight"]


def catalog_roles(slug):
    products_by_slug = {
        product["slug"]: product
        for product in PRODUCTS
    }

    return products_by_slug[slug]["roles"]


class ScoringTests(APITestCase):
    def test_score_products_applies_play_style_bonus_without_crashing(self):
        product = create_product("m4-aeg")

        results = score_products(
            products=Product.objects.all(),
            answers=quiz_answers(
                experience="novice",
                maintenance="no",
                simple_start="yes",
            ),
        )

        self.assertEqual(results[0]["product"], product)
        self.assertIn("match_percent", results[0])

    def test_play_style_bonus_uses_product_roles_not_slug_list(self):
        role_match = create_product("custom-cqb-platform", roles=["cqb"])
        create_product("custom-field-platform", roles=["field"])

        results = score_products(
            products=Product.objects.all(),
            answers=quiz_answers(
                play_style="cqb",
            ),
        )

        self.assertEqual(results[0]["product"], role_match)

    def test_play_role_adds_smaller_secondary_role_bonus(self):
        sniper_role = create_product("sniper-role", roles=["field", "sniper"])
        create_product("field-only", roles=["field"])

        results = score_products(
            products=Product.objects.order_by("slug"),
            answers=quiz_answers(
                play_role="sniper",
            ),
            top_n=2,
        )

        self.assertEqual(results[0]["product"], sniper_role)
        self.assertEqual(
            results[0]["score"] - results[1]["score"],
            PLAY_ROLE_BONUS_POINTS,
        )

    def test_play_role_does_not_reuse_play_style_tags(self):
        create_product("legacy-cqb-tag", roles=["field", "cqb"])
        create_product("field-only", roles=["field"])

        results = score_products(
            products=Product.objects.order_by("slug"),
            answers=quiz_answers(
                play_role="cqb",
            ),
            top_n=2,
        )

        self.assertEqual(results[0]["score"], results[1]["score"])

    def test_product_goal_prefers_sidearms_when_requested(self):
        sidearm = create_product("glock-gbb", type="GBB", roles=["field"])
        create_product("field-aeg", roles=["field"])

        results = score_products(
            products=Product.objects.order_by("slug"),
            answers=quiz_answers(
                product_goal="sidearm",
                priority="ergonomics",
            ),
            top_n=2,
        )

        self.assertEqual(results[0]["product"], sidearm)

    def test_product_goal_any_is_explicitly_neutral(self):
        create_product("field-aeg", roles=["field"])
        create_product("other-field-aeg", roles=["field"])

        results = score_products(
            products=Product.objects.order_by("slug"),
            answers=quiz_answers(product_goal="any"),
            top_n=2,
        )

        self.assertEqual(results[0]["score"], results[1]["score"])

    def test_product_goal_rejects_unsupported_values(self):
        create_product("field-aeg", roles=["field"])

        with self.assertRaisesMessage(KeyError, "Unsupported product_goal"):
            score_products(
                products=Product.objects.all(),
                answers=quiz_answers(product_goal="unknown_goal"),
            )

    def test_cold_weather_penalizes_gas_platforms(self):
        aeg = create_product("field-aeg", roles=["field"])
        create_product("field-gbbr", type="GBBR", roles=["field"])

        results = score_products(
            products=Product.objects.order_by("slug"),
            answers=quiz_answers(
                experience="few_games",
                product_goal="primary",
                priority="realism",
                weather="cold",
            ),
            top_n=2,
        )

        self.assertEqual(results[0]["product"], aeg)

    def test_minimal_extra_gear_penalizes_hpa_platforms(self):
        aeg = create_product("field-aeg", roles=["field"])
        create_product("field-hpa", type="HPA", roles=["field"])

        results = score_products(
            products=Product.objects.order_by("slug"),
            answers=quiz_answers(
                product_goal="primary",
                priority="ergonomics",
                extra_gear="minimal",
            ),
            top_n=2,
        )

        self.assertEqual(results[0]["product"], aeg)

    def test_tuning_yes_rewards_upgrade_potential(self):
        upgradeable = create_product(
            "upgradeable-aeg",
            scores={
                **FULL_SCORES,
                "upgrade_potential": 10,
            },
        )
        create_product(
            "stock-aeg",
            scores={
                **FULL_SCORES,
                "upgrade_potential": 2,
            },
        )

        results = score_products(
            products=Product.objects.order_by("slug"),
            answers=quiz_answers(tuning="yes"),
            top_n=2,
        )

        self.assertEqual(results[0]["product"], upgradeable)
        self.assertAlmostEqual(results[0]["score"] - results[1]["score"], 2.8)

    def test_tuning_no_does_not_reward_upgrade_potential(self):
        create_product(
            "upgradeable-aeg",
            scores={
                **FULL_SCORES,
                "upgrade_potential": 10,
            },
        )
        create_product(
            "stock-aeg",
            scores={
                **FULL_SCORES,
                "upgrade_potential": 2,
            },
        )

        results = score_products(
            products=Product.objects.order_by("slug"),
            answers=quiz_answers(tuning="no"),
            top_n=2,
        )

        self.assertEqual(results[0]["score"], results[1]["score"])

    def test_novice_experience_does_not_double_count_simple_start_bonus(self):
        create_product("m4-aeg", roles=["field"])
        create_product("generic-aeg", roles=["field"])

        without_simple_start = score_products(
            products=Product.objects.order_by("slug"),
            answers=quiz_answers(
                experience="novice",
                simple_start="no",
            ),
            top_n=2,
        )
        without_scores = {
            item["product"].slug: item["score"]
            for item in without_simple_start
        }

        with_simple_start = score_products(
            products=Product.objects.order_by("slug"),
            answers=quiz_answers(
                experience="novice",
                simple_start="yes",
            ),
            top_n=2,
        )
        with_scores = {
            item["product"].slug: item["score"]
            for item in with_simple_start
        }

        self.assertEqual(without_scores["m4-aeg"], without_scores["generic-aeg"])
        self.assertEqual(
            with_scores["m4-aeg"] - with_scores["generic-aeg"],
            BEGINNER_PLATFORM_BONUS_POINTS,
        )

    def test_match_percent_uses_fixed_business_max_score(self):
        create_product(
            "weak-spring",
            type="Spring",
            roles=[],
            scores={
                "reliability": 1,
                "repair_cost": 1,
                "beginner_friendly": 1,
                "status": 1,
                "drive": 1,
                "comfort": 1,
                "weight": 1,
                "cqb": 1,
                "upgrade_potential": 1,
            },
        )

        results = score_products(
            products=Product.objects.all(),
            answers=quiz_answers(
                simple_start="yes",
            ),
        )

        expected_percent = int((results[0]["score"] / MAX_SCORE) * 100)

        self.assertEqual(results[0]["score"], 1)
        self.assertEqual(results[0]["match_percent"], expected_percent)
        self.assertLess(results[0]["match_percent"], 100)

    def test_realism_priority_does_not_require_realism_score(self):
        product = create_product(
            "mws-m4-gbbr",
            type="GBBR",
            scores={
                "reliability": 8,
                "repair_cost": 6,
                "beginner_friendly": 5,
                "status": 9,
                "drive": 9,
                "comfort": 7,
                "weight": 7,
                "cqb": 5,
                "upgrade_potential": 7,
            },
        )

        results = score_products(
            products=Product.objects.all(),
            answers=quiz_answers(
                play_style="milsim",
                play_role="sniper",
                priority="realism",
                budget="high",
                maintenance="yes",
            ),
        )

        self.assertEqual(results[0]["product"], product)
        self.assertNotIn("realism", product.scores)
        self.assertIn("match_percent", results[0])

    def test_ergonomics_priority_includes_weight_score(self):
        light_product = create_product(
            "light-aeg",
            scores={
                "reliability": 7,
                "repair_cost": 7,
                "beginner_friendly": 7,
                "status": 5,
                "drive": 6,
                "comfort": 6,
                "weight": 10,
                "cqb": 8,
                "upgrade_potential": 7,
            },
        )
        create_product(
            "heavy-aeg",
            scores={
                "reliability": 7,
                "repair_cost": 7,
                "beginner_friendly": 7,
                "status": 5,
                "drive": 6,
                "comfort": 8,
                "weight": 2,
                "cqb": 8,
                "upgrade_potential": 7,
            },
        )

        results = score_products(
            products=Product.objects.all(),
            answers=quiz_answers(
                priority="ergonomics",
                weight="important",
            ),
        )

        self.assertEqual(results[0]["product"], light_product)

    def test_score_products_rejects_non_numeric_score_values(self):
        create_product(
            "invalid-score-aeg",
            scores={
                "reliability": "high",
                "repair_cost": 8,
                "beginner_friendly": 8,
                "status": 6,
                "drive": 6,
                "comfort": 8,
                "weight": 8,
                "cqb": 8,
                "upgrade_potential": 7,
            },
        )

        with self.assertRaisesMessage(ValueError, "нечислове поле"):
            score_products(
                products=Product.objects.all(),
                answers=quiz_answers(),
            )

    def test_score_products_rejects_out_of_range_score_values(self):
        create_product(
            "out-of-range-score-aeg",
            scores={
                "reliability": 11,
                "repair_cost": 8,
                "beginner_friendly": 8,
                "status": 6,
                "drive": 6,
                "comfort": 8,
                "weight": 8,
                "cqb": 8,
                "upgrade_potential": 7,
            },
        )

        with self.assertRaisesMessage(ValueError, "очікується значення від 1 до 10"):
            score_products(
                products=Product.objects.all(),
                answers=quiz_answers(),
            )

    def test_score_products_requires_new_quiz_answers_without_fallbacks(self):
        create_product("m4-aeg")

        for field in ("product_goal", "tuning", "weather", "extra_gear"):
            with self.subTest(field=field):
                answers = quiz_answers(
                    experience="novice",
                    maintenance="no",
                    simple_start="yes",
                )
                del answers[field]

                with self.assertRaises(KeyError):
                    score_products(
                        products=Product.objects.all(),
                        answers=answers,
                    )


class ProductCatalogDataTests(APITestCase):
    def test_catalog_products_include_semantic_play_role_tags(self):
        self.assertIn("assault", catalog_roles("m4-aeg"))
        self.assertIn("sniper", catalog_roles("tm-vsr10"))
        self.assertIn("sniper", catalog_roles("hk417-gbbr"))
        self.assertIn("sniper", catalog_roles("sr25-gbbr"))
        self.assertIn("sniper", catalog_roles("m110-gbbr"))
        self.assertIn("support", catalog_roles("m249-saw"))
        self.assertIn("field", catalog_roles("m4-aeg"))

    def test_quiz_play_role_uses_semantic_values(self):
        play_role_question = next(
            question
            for question in QUIZ_QUESTIONS
            if question["id"] == "play_role"
        )
        values = {
            option["value"]
            for option in play_role_question["options"]
        }

        self.assertEqual(values, {"assault", "sniper", "support"})

    def test_quiz_includes_product_goal_tuning_weather_and_extra_gear(self):
        questions_by_id = {
            question["id"]: question
            for question in QUIZ_QUESTIONS
        }

        self.assertEqual(
            {
                option["value"]
                for option in questions_by_id["product_goal"]["options"]
            },
            {"primary", "sidearm", "sniper_platform", "support_platform", "any"},
        )
        self.assertEqual(
            {
                option["value"]
                for option in questions_by_id["weather"]["options"]
            },
            {"warm", "cold", "mixed"},
        )
        self.assertEqual(
            {
                option["value"]
                for option in questions_by_id["tuning"]["options"]
            },
            {"no", "basic", "yes"},
        )
        self.assertEqual(
            {
                option["value"]
                for option in questions_by_id["extra_gear"]["options"]
            },
            {"minimal", "some", "ready"},
        )

    def test_weight_scores_follow_platform_weight_classes(self):
        self.assertGreater(
            catalog_weight("glock-18c"),
            catalog_weight("desert-eagle"),
        )
        self.assertGreater(
            catalog_weight("aap-01-assassin"),
            catalog_weight("m4-aeg"),
        )
        self.assertGreater(
            catalog_weight("m4-aeg"),
            catalog_weight("m249-saw"),
        )
        self.assertGreater(
            catalog_weight("m249-saw"),
            catalog_weight("mg42"),
        )

    def test_calibrated_scores_follow_realistic_platform_tradeoffs(self):
        m4_aeg = catalog_scores("m4-aeg")
        mws_gbbr = catalog_scores("mws-m4-gbbr")
        glock = catalog_scores("glock-18c")
        desert_eagle = catalog_scores("desert-eagle")
        mp5k = catalog_scores("mp5k-aeg")
        m249 = catalog_scores("m249-saw")
        tm_vsr = catalog_scores("tm-vsr10")

        self.assertGreater(m4_aeg["beginner_friendly"], mws_gbbr["beginner_friendly"])
        self.assertGreater(mws_gbbr["drive"], m4_aeg["drive"])
        self.assertGreater(tm_vsr["repair_cost"], mws_gbbr["repair_cost"])
        self.assertGreater(mp5k["cqb"], m249["cqb"])
        self.assertGreater(glock["comfort"], desert_eagle["comfort"])
        self.assertLess(desert_eagle["beginner_friendly"], glock["beginner_friendly"])

    def test_catalog_scores_include_upgrade_potential(self):
        self.assertGreater(catalog_scores("tm-vsr10")["upgrade_potential"], 8)
        self.assertGreater(catalog_scores("m4-aeg")["upgrade_potential"], 8)
        self.assertLess(catalog_scores("desert-eagle")["upgrade_potential"], 5)


class ProductApiTests(APITestCase):
    def test_product_list_filters_by_role_on_sqlite(self):
        create_product("m4-aeg", roles=["field", "cqb"])
        create_product("ak-aeg", roles=["field"])

        response = self.client.get(reverse("product-list"), {"role": "cqb"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["slug"], "m4-aeg")

    def test_filters_include_semantic_play_role_tags(self):
        response = self.client.get(reverse("filters"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("assault", response.data["roles"])
        self.assertIn("sniper", response.data["roles"])
        self.assertIn("support", response.data["roles"])

    def test_invalid_ordering_does_not_crash_product_list(self):
        create_product("m4-aeg")

        response = self.client.get(
            reverse("product-list"),
            {"ordering": "bad_field"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_compare_products_returns_requested_products(self):
        create_product("m4-aeg")
        create_product("ak-aeg")
        create_product("mp5-aeg")

        response = self.client.get(
            reverse("products-compare"),
            {"slugs": "m4-aeg,ak-aeg,mp5-aeg"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["products"]), 3)


class QuizApiTests(APITestCase):
    def test_quiz_submit_returns_recommendations_and_saves_submission(self):
        create_product("m4-aeg", roles=["field", "cqb"])
        create_product("ak-aeg", roles=["field"])

        response = self.client.post(
            reverse("quiz-submit"),
            {
                "experience": "novice",
                "product_goal": "primary",
                "play_style": "field",
                "play_role": "assault",
                "priority": "reliability",
                "budget": "medium",
                "maintenance": "no",
                "tuning": "no",
                "weight": "not_important",
                "weather": "mixed",
                "extra_gear": "minimal",
                "simple_start": "yes",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(QuizSubmission.objects.count(), 1)

    def test_quiz_submit_rejects_unknown_choice(self):
        create_product("m4-aeg")

        response = self.client.post(
            reverse("quiz-submit"),
            {
                "experience": "unknown",
                "product_goal": "primary",
                "play_style": "field",
                "play_role": "assault",
                "priority": "reliability",
                "budget": "medium",
                "maintenance": "no",
                "tuning": "no",
                "weight": "not_important",
                "weather": "mixed",
                "extra_gear": "minimal",
                "simple_start": "yes",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("experience", response.data)

    def test_quiz_submit_requires_new_quiz_fields(self):
        create_product("m4-aeg")

        for field in ("product_goal", "tuning", "weather", "extra_gear"):
            with self.subTest(field=field):
                payload = {
                    "experience": "novice",
                    "product_goal": "primary",
                    "play_style": "field",
                    "play_role": "assault",
                    "priority": "reliability",
                    "budget": "medium",
                    "maintenance": "no",
                    "tuning": "no",
                    "weight": "not_important",
                    "weather": "mixed",
                    "extra_gear": "minimal",
                    "simple_start": "yes",
                }
                del payload[field]

                response = self.client.post(
                    reverse("quiz-submit"),
                    payload,
                    format="json",
                )

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(field, response.data)

    def test_quiz_submit_rejects_old_play_role_choice(self):
        create_product("m4-aeg")

        response = self.client.post(
            reverse("quiz-submit"),
            {
                "experience": "novice",
                "product_goal": "primary",
                "play_style": "field",
                "play_role": "cqb",
                "priority": "reliability",
                "budget": "medium",
                "maintenance": "no",
                "tuning": "no",
                "weight": "not_important",
                "weather": "mixed",
                "extra_gear": "minimal",
                "simple_start": "yes",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("play_role", response.data)

    def test_quiz_submit_returns_controlled_error_for_incomplete_scores(self):
        create_product(
            "broken-aeg",
            scores={
                "reliability": 8,
            },
        )

        response = self.client.post(
            reverse("quiz-submit"),
            {
                "experience": "novice",
                "product_goal": "primary",
                "play_style": "field",
                "play_role": "assault",
                "priority": "reliability",
                "budget": "medium",
                "maintenance": "no",
                "tuning": "no",
                "weight": "not_important",
                "weather": "mixed",
                "extra_gear": "minimal",
                "simple_start": "yes",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["detail"], "Product scoring data is incomplete.")
        self.assertIn("broken-aeg", response.data["error"])
