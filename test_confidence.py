"""Unit tests for confidence.py — validate scoring, combination, edge cases."""

import sqlite3
import unittest

from confidence import (
    ConfidenceScore, score, combine, explain, category,
    populate_source_table, record, SOURCE_BASELINES,
)


# ---------------------------------------------------------------- ConfidenceScore

class TestConfidenceScore(unittest.TestCase):

    def test_basic_construction(self):
        c = ConfidenceScore(value=0.8, source="test", rationale="ok")
        self.assertEqual(c.value, 0.8)
        self.assertEqual(c.source, "test")
        self.assertEqual(c.category, "HIGH")

    def test_value_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            ConfidenceScore(value=1.5, source="x", rationale="y")
        with self.assertRaises(ValueError):
            ConfidenceScore(value=-0.1, source="x", rationale="y")

    def test_category_boundaries(self):
        self.assertEqual(category(0.0),  "LOW")
        self.assertEqual(category(0.59), "LOW")
        self.assertEqual(category(0.60), "MEDIUM")
        self.assertEqual(category(0.79), "MEDIUM")
        self.assertEqual(category(0.80), "HIGH")
        self.assertEqual(category(0.94), "HIGH")
        self.assertEqual(category(0.95), "VERY HIGH")
        self.assertEqual(category(1.00), "VERY HIGH")

    def test_value_must_be_numeric(self):
        with self.assertRaises(TypeError):
            ConfidenceScore(value="0.5", source="x", rationale="y")


# ---------------------------------------------------------------- score()

class TestScorePhylo(unittest.TestCase):
    """Phylogenetic identity scoring per addendum 3 brackets."""

    def test_species_level(self):
        c = score("phylo_16s", "identity_pct", 99.5)
        self.assertGreaterEqual(c.value, 0.90)
        self.assertLessEqual(c.value, 0.95)
        self.assertEqual(c.category, "HIGH")  # 0.90-0.95 boundary

    def test_perfect_match_top_of_band(self):
        c = score("phylo_16s", "identity_pct", 100.0)
        self.assertAlmostEqual(c.value, 0.95)

    def test_genus_level(self):
        c = score("phylo_16s", "identity_pct", 96.1)
        # 90-97 → 0.70-0.90; at 96.1 we expect ~0.87
        self.assertGreater(c.value, 0.80)
        self.assertLess(c.value, 0.90)

    def test_family_level(self):
        c = score("phylo_16s", "identity_pct", 87.0)
        self.assertGreaterEqual(c.value, 0.50)
        self.assertLess(c.value, 0.70)

    def test_phylum_level_recommends_tier_2_3(self):
        c = score("phylo_16s", "identity_pct", 78.0)
        self.assertLess(c.value, 0.50)
        self.assertEqual(c.category, "LOW")
        self.assertIn("Tier", c.rationale)

    def test_floor_at_30(self):
        c = score("phylo_16s", "identity_pct", 50.0)
        self.assertEqual(c.value, 0.30)

    def test_monotonically_non_decreasing(self):
        prev = 0.0
        for ident in range(70, 101):
            v = score("phylo_16s", "identity_pct", float(ident)).value
            self.assertGreaterEqual(v, prev - 1e-9,
                                    f"score decreased at identity={ident}")
            prev = v


class TestScoreGapseq(unittest.TestCase):

    def test_complete_with_predicted(self):
        c = score("gapseq", "pathway_completeness", 100.0,
                  context={"predicted": True})
        self.assertGreaterEqual(c.value, 0.90)

    def test_incomplete_with_predicted_still_high(self):
        c = score("gapseq", "pathway_completeness", 80.0,
                  context={"predicted": True})
        self.assertGreaterEqual(c.value, 0.70)

    def test_high_completeness_no_predicted(self):
        c = score("gapseq", "pathway_completeness", 88.0,
                  context={"predicted": False})
        # ≥75 with predicted=false: 0.70-0.90 band
        self.assertGreaterEqual(c.value, 0.70)
        self.assertLessEqual(c.value, 0.90)

    def test_partial(self):
        c = score("gapseq", "pathway_completeness", 60.0,
                  context={"predicted": False})
        self.assertGreaterEqual(c.value, 0.40)
        self.assertLess(c.value, 0.70)

    def test_weak(self):
        c = score("gapseq", "pathway_completeness", 20.0,
                  context={"predicted": False})
        self.assertGreaterEqual(c.value, 0.20)
        self.assertLess(c.value, 0.40)


class TestScoreBaseline(unittest.TestCase):

    def test_fixed_baseline(self):
        c = score("mediadive", "anything", None)
        self.assertEqual(c.value, 0.95)

    def test_user_supplied(self):
        c = score("user_supplied", "anything", None)
        self.assertEqual(c.value, 0.95)

    def test_range_baseline_with_quality(self):
        # mebipred: (0.50, 0.90); raw_value=1 should hit top
        c = score("mebipred", "binding_probability", 1.0)
        self.assertEqual(c.value, 0.90)
        c = score("mebipred", "binding_probability", 0.0)
        self.assertEqual(c.value, 0.50)
        c = score("mebipred", "binding_probability", 0.5)
        self.assertEqual(c.value, 0.70)

    def test_unknown_source_returns_default(self):
        c = score("nonexistent", "anything", 0.5)
        self.assertEqual(c.value, 0.50)
        self.assertIn("unknown source", c.rationale)


# ---------------------------------------------------------------- combine()

class TestCombineEdgeCases(unittest.TestCase):

    def test_empty_returns_zero(self):
        c = combine("min", [])
        self.assertEqual(c.value, 0.0)
        self.assertEqual(c.context.get("n"), 0)

    def test_single_score_passes_through(self):
        s = ConfidenceScore(value=0.73, source="x", rationale="r")
        c = combine("min", [s])
        self.assertEqual(c.value, 0.73)
        self.assertEqual(c.source, "x")  # original returned unchanged

    def test_unknown_method_raises(self):
        s = ConfidenceScore(value=0.5, source="x", rationale="r")
        with self.assertRaises(ValueError):
            combine("xyzzy", [s, s])


class TestCombineMethods(unittest.TestCase):

    def setUp(self):
        self.high = ConfidenceScore(value=0.90, source="A", rationale="a")
        self.med  = ConfidenceScore(value=0.70, source="B", rationale="b")
        self.low  = ConfidenceScore(value=0.40, source="C", rationale="c")

    def test_min(self):
        c = combine("min", [self.high, self.med, self.low])
        self.assertEqual(c.value, 0.40)

    def test_mean(self):
        c = combine("mean", [self.high, self.med, self.low])
        self.assertAlmostEqual(c.value, (0.90 + 0.70 + 0.40) / 3)

    def test_weighted_mean(self):
        c = combine("weighted_mean",
                    [self.high, self.med, self.low],
                    weights=[1.0, 1.0, 1.0])
        self.assertAlmostEqual(c.value, (0.90 + 0.70 + 0.40) / 3)

    def test_weighted_mean_skewed(self):
        # weight high-source heavily → result should pull up toward high
        c = combine("weighted_mean", [self.high, self.low], weights=[3.0, 1.0])
        self.assertAlmostEqual(c.value, (3 * 0.90 + 1 * 0.40) / 4)

    def test_weighted_mean_validation(self):
        with self.assertRaises(ValueError):
            combine("weighted_mean", [self.high, self.med])  # no weights
        with self.assertRaises(ValueError):
            combine("weighted_mean", [self.high, self.med], weights=[1.0])
        with self.assertRaises(ValueError):
            combine("weighted_mean", [self.high, self.med], weights=[0.0, 0.0])

    def test_independent(self):
        # Two independent 0.5 sources: 1 - 0.5*0.5 = 0.75
        a = ConfidenceScore(value=0.5, source="A", rationale="")
        b = ConfidenceScore(value=0.5, source="B", rationale="")
        c = combine("independent", [a, b])
        self.assertAlmostEqual(c.value, 0.75)

    def test_independent_three_evidence(self):
        # 0.5, 0.5, 0.5 → 1 - 0.125 = 0.875
        s = ConfidenceScore(value=0.5, source="", rationale="")
        c = combine("independent", [s, s, s])
        self.assertAlmostEqual(c.value, 0.875)


class TestAgreementBonus(unittest.TestCase):

    def test_agreement_bonus_applied_when_close(self):
        # 0.85 + 0.88 + 0.86 → all within 0.10 → +0.05 bonus
        s1 = ConfidenceScore(value=0.85, source="A", rationale="")
        s2 = ConfidenceScore(value=0.88, source="B", rationale="")
        s3 = ConfidenceScore(value=0.86, source="C", rationale="")
        c = combine("min", [s1, s2, s3], agreement_bonus=True)
        # min is 0.85 + 0.05 bonus = 0.90
        self.assertAlmostEqual(c.value, 0.90)
        self.assertIn("agreement bonus", c.rationale)
        self.assertTrue(c.context["agreement_bonus_applied"])

    def test_agreement_bonus_not_applied_when_disagree(self):
        # 0.30 vs 0.90 → no bonus
        s1 = ConfidenceScore(value=0.30, source="A", rationale="")
        s2 = ConfidenceScore(value=0.90, source="B", rationale="")
        c = combine("min", [s1, s2], agreement_bonus=True)
        self.assertEqual(c.value, 0.30)
        self.assertFalse(c.context["agreement_bonus_applied"])

    def test_agreement_bonus_caps_at_95(self):
        # 0.93 + 0.94 → min=0.93 + 0.05 would be 0.98, but capped
        s1 = ConfidenceScore(value=0.93, source="A", rationale="")
        s2 = ConfidenceScore(value=0.94, source="B", rationale="")
        c = combine("min", [s1, s2], agreement_bonus=True)
        self.assertLessEqual(c.value, 0.95)


# ---------------------------------------------------------------- explain

class TestExplain(unittest.TestCase):

    def test_basic(self):
        c = ConfidenceScore(value=0.83, source="gapseq",
                            rationale="pathway 87%")
        self.assertEqual(explain(c), "83% [HIGH] — pathway 87%")

    def test_brief(self):
        c = ConfidenceScore(value=0.50, source="x", rationale="r")
        self.assertEqual(explain(c, brief=True), "50% [LOW]")

    def test_round_trip(self):
        for v in (0.0, 0.30, 0.60, 0.80, 0.95, 1.00):
            c = ConfidenceScore(value=v, source="t", rationale="r")
            self.assertIn(c.category, explain(c))


# ---------------------------------------------------------------- DB integration

class TestDBIntegration(unittest.TestCase):

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")

    def tearDown(self):
        self.conn.close()

    def test_populate_source_table_idempotent(self):
        n1 = populate_source_table(self.conn)
        n2 = populate_source_table(self.conn)
        self.assertEqual(n1, n2)
        self.assertGreater(n1, 0)
        rows = self.conn.execute(
            "SELECT COUNT(*) FROM source_confidence"
        ).fetchone()[0]
        self.assertEqual(rows, n1)

    def test_subtype_split(self):
        populate_source_table(self.conn)
        row = self.conn.execute(
            "SELECT subtype, baseline_min FROM source_confidence "
            "WHERE source_name='bacdive' AND subtype='experimental'"
        ).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "experimental")
        self.assertEqual(row[1], 0.90)

    def test_record_persists(self):
        populate_source_table(self.conn)
        c = score("phylo_16s", "identity_pct", 95.0)
        rid = record(self.conn, "phylo_hit", c,
                     related_table="organisms", related_id=4414)
        self.assertGreater(rid, 0)
        row = self.conn.execute(
            "SELECT prediction_type, source, computed_confidence, "
            "       related_table, related_id "
            "FROM prediction_confidences WHERE id=?", (rid,)
        ).fetchone()
        self.assertEqual(row[0], "phylo_hit")
        self.assertEqual(row[1], "phylo_16s")
        self.assertAlmostEqual(row[2], c.value)
        self.assertEqual(row[3], "organisms")
        self.assertEqual(row[4], 4414)


# ---------------------------------------------------------------- realistic scenarios

class TestRealisticScenarios(unittest.TestCase):
    """Emulate the kinds of compositions the system will actually do."""

    def test_recipe_min_with_agreement_for_prototroph(self):
        """A prototroph on rich medium: phylo HIGH + thermal HIGH + medium HIGH."""
        phylo = score("phylo_16s", "identity_pct", 99.7)
        thermal = score("thermal", "class_match", None,
                        context={"query_class": "mesophile",
                                 "hit_class": "mesophile"})
        medium = ConfidenceScore(value=0.95, source="mediadive",
                                  rationale="curated medium")
        overall = combine("min", [phylo, thermal, medium], agreement_bonus=True)
        self.assertGreaterEqual(overall.value, 0.85,
                                f"prototroph recipe should be HIGH, got {overall.value}")

    def test_recipe_with_uncertain_component_drags_down(self):
        """Min combination correctly surfaces the weakest link."""
        strong = ConfidenceScore(value=0.92, source="A", rationale="")
        strong2 = ConfidenceScore(value=0.90, source="B", rationale="")
        weak = ConfidenceScore(value=0.55, source="C", rationale="")
        overall = combine("min", [strong, strong2, weak])
        self.assertEqual(overall.value, 0.55)

    def test_disagreement_drops_to_lower(self):
        """When sources disagree (per addendum: temp inference vs. user override
           kind of case), agreement bonus should NOT apply."""
        tempura_says = ConfidenceScore(value=0.85, source="tempura", rationale="")
        genomespot_says = ConfidenceScore(value=0.40, source="genomespot",
                                          rationale="")
        c = combine("min", [tempura_says, genomespot_says], agreement_bonus=True)
        self.assertEqual(c.value, 0.40)
        self.assertFalse(c.context["agreement_bonus_applied"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
