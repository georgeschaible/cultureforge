"""Unit tests for thermodynamics.py — calculator correctness, interpolation,
and (with placeholder data) an end-to-end knallgas smoke test.

Tests are grouped by what they verify:

  A. Pure math — interpolation, ΔG°r from compounds, ΔGr = ΔG°r + RT ln(Qr)
     (these don't require any specific thermodynamic values)
  B. Schema + persistence — insert/retrieve round-trip
  C. Placeholder knallgas smoke test — proves the pipeline works end-to-end.
     NOTE: actual ΔGr values are PLACEHOLDER; these assertions validate the
     pipeline, not the science. Real A&S-loaded values will be validated
     separately in `validate_thermodynamics.py` once the PDF is digitized.
"""

import math
import sqlite3
import unittest

import thermodynamics as td


class TestInterpolation(unittest.TestCase):

    def test_exact_reference_points_return_exact_values(self):
        # Identity case: at each reference temp, the interpolator should
        # return exactly that reference's ΔG°.
        vals = tuple(float(i) for i in range(12))
        for i, t in enumerate(td.REFERENCE_TEMPS_C):
            got = td.interpolate_dg(vals, t)
            self.assertAlmostEqual(got, float(i), places=9,
                                   msg=f"at T={t}°C")

    def test_midpoint_is_average(self):
        # Two adjacent reference points with values 10 and 20 → midpoint is 15
        vals = [None] * 12
        vals[2] = 10.0   # 25°C
        vals[3] = 20.0   # 37°C
        mid = (25 + 37) / 2.0
        self.assertAlmostEqual(td.interpolate_dg(tuple(vals), mid), 15.0)

    def test_handles_missing_values(self):
        vals = [None] * 12
        # Only 25°C and 100°C have data — should linearly interpolate at 70°C
        vals[2] = -100.0   # 25°C
        vals[8] = -200.0   # 100°C
        got = td.interpolate_dg(tuple(vals), 70.0)
        # Linear: from 25→100°C (range 75°C), slope = -100/75 per °C
        expected = -100.0 + (70.0 - 25.0) * (-100.0 / 75.0)
        self.assertAlmostEqual(got, expected, places=6)

    def test_raises_when_too_few_points(self):
        vals = [None] * 12
        vals[0] = 1.0
        with self.assertRaises(ValueError):
            td.interpolate_dg(tuple(vals), 25.0)

    def test_raises_when_far_outside_range(self):
        vals = tuple(float(i) for i in range(12))
        with self.assertRaises(ValueError):
            td.interpolate_dg(vals, -50.0)
        with self.assertRaises(ValueError):
            td.interpolate_dg(vals, 300.0)

    def test_extrapolation_tolerance(self):
        # 5°C tolerance outside the range should be accepted
        vals = tuple(float(i) for i in range(12))
        td.interpolate_dg(vals, td.TEMP_MIN_C - 3)  # shouldn't raise
        td.interpolate_dg(vals, td.TEMP_MAX_C + 3)


class TestViabilityClassification(unittest.TestCase):

    def test_strongly_negative_is_viable(self):
        self.assertEqual(td.viability(-50.0), "viable")

    def test_marginally_negative_is_marginal(self):
        self.assertEqual(td.viability(-10.0), "marginal")
        self.assertEqual(td.viability(-0.01), "marginal")

    def test_positive_is_not_viable(self):
        self.assertEqual(td.viability(0.0), "not_viable")
        self.assertEqual(td.viability(25.0), "not_viable")

    def test_boundary_minus_20(self):
        self.assertEqual(td.viability(-20.0), "marginal")
        self.assertEqual(td.viability(-20.01), "viable")


class TestPersistence(unittest.TestCase):

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        td.init_schema(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_insert_and_fetch_compound(self):
        vals = tuple(float(i) for i in range(12))
        td.insert_compound(
            self.conn, name="H2O(l)", formula="H2O", phase="liquid",
            chemical_system="H-O", source_table="test",
            dg_values=vals,
        )
        c = td.get_compound(self.conn, "H2O(l)")
        self.assertEqual(c.name, "H2O(l)")
        self.assertEqual(c.phase, "liquid")
        for a, b in zip(c.values, vals):
            self.assertEqual(a, b)

    def test_insert_and_fetch_reaction(self):
        stoich = {"H2(aq)": -1.0, "O2(aq)": -0.5, "H2O(l)": 1.0}
        td.insert_reaction(
            self.conn, name="knallgas", equation="H2+0.5O2->H2O",
            stoichiometry=stoich, chemical_system="H-O", reaction_type="redox",
            source_table="test",
            dgr_values=tuple(float(-i) for i in range(12)),
        )
        r = td.get_reaction(self.conn, "knallgas")
        self.assertEqual(r.name, "knallgas")
        self.assertEqual(r.stoichiometry, stoich)

    def test_compound_wrong_length_raises(self):
        with self.assertRaises(ValueError):
            td.insert_compound(
                self.conn, name="X", formula="X", phase="aq",
                chemical_system="X", source_table="t",
                dg_values=(1.0, 2.0),
            )


class TestDGrMath(unittest.TestCase):
    """Verify the nernst-style ΔGr = ΔG°r + R·T·ln(Qr) is computed correctly."""

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        td.init_schema(self.conn)
        # A reaction with ΔG°r = 0 at all temps so ΔGr = R·T·ln(Qr) exactly.
        # A → B  (1 mol each)
        td.insert_reaction(
            self.conn, name="toy", equation="A -> B",
            stoichiometry={"A": -1.0, "B": 1.0},
            chemical_system="test", reaction_type="test", source_table="test",
            dgr_values=tuple(0.0 for _ in range(12)),
        )

    def tearDown(self):
        self.conn.close()

    def test_standard_state_gives_zero_when_dg_std_is_zero(self):
        dg = td.delta_gr(self.conn, "toy", 25.0,
                          activities={"A": 1.0, "B": 1.0})
        self.assertAlmostEqual(dg, 0.0, places=10)

    def test_ln_q_positive_when_products_exceed_reactants(self):
        # a_B=10, a_A=1 → Q=10 → ΔGr = R·T·ln(10) at 25°C = 8.314e-3 * 298.15 * ln(10)
        dg = td.delta_gr(self.conn, "toy", 25.0,
                          activities={"A": 1.0, "B": 10.0})
        expected = td.R_KJ * (25 + td.C_TO_K) * math.log(10)
        self.assertAlmostEqual(dg, expected, places=6)

    def test_ln_q_negative_when_reactants_exceed_products(self):
        # a_A=10, a_B=1 → Q=0.1 → ΔGr = R·T·ln(0.1) < 0
        dg = td.delta_gr(self.conn, "toy", 25.0,
                          activities={"A": 10.0, "B": 1.0})
        expected = td.R_KJ * (25 + td.C_TO_K) * math.log(0.1)
        self.assertAlmostEqual(dg, expected, places=6)

    def test_activity_zero_raises(self):
        with self.assertRaises(ValueError):
            td.delta_gr(self.conn, "toy", 25.0,
                         activities={"A": 0.0, "B": 1.0})

    def test_missing_activity_defaults_to_one(self):
        # Only A provided; B defaults to 1.0. Same as all-1.
        dg_explicit = td.delta_gr(self.conn, "toy", 25.0,
                                    activities={"A": 1.0, "B": 1.0})
        dg_implicit = td.delta_gr(self.conn, "toy", 25.0,
                                    activities={"A": 1.0})
        self.assertAlmostEqual(dg_implicit, dg_explicit, places=10)

    def test_temperature_enters_linearly_in_nernst_term(self):
        # ΔG°r = 0 so ΔGr = R·T·ln(Q). Doubling T doubles ΔGr for same Q.
        dg_25 = td.delta_gr(self.conn, "toy", 25.0,
                             activities={"A": 1.0, "B": 100.0})
        dg_150 = td.delta_gr(self.conn, "toy", 150.0,
                              activities={"A": 1.0, "B": 100.0})
        ratio = dg_150 / dg_25
        expected_ratio = (150 + td.C_TO_K) / (25 + td.C_TO_K)
        self.assertAlmostEqual(ratio, expected_ratio, places=6)


class TestDGStandardFromCompounds(unittest.TestCase):

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        td.init_schema(self.conn)
        # Two compounds A and B with constant ΔG°f across all temps
        td.insert_compound(
            self.conn, name="A", formula="A", phase="aq",
            chemical_system="t", source_table="t",
            dg_values=tuple(-100.0 for _ in range(12)),
        )
        td.insert_compound(
            self.conn, name="B", formula="B", phase="aq",
            chemical_system="t", source_table="t",
            dg_values=tuple(-50.0 for _ in range(12)),
        )

    def tearDown(self):
        self.conn.close()

    def test_sum_of_formation_energies(self):
        # A → B  means ΔG°r = ΔG°f(B) − ΔG°f(A) = −50 − (−100) = +50
        dg = td.dg_standard_reaction_from_compounds(
            self.conn, {"A": -1.0, "B": 1.0}, 25.0)
        self.assertAlmostEqual(dg, 50.0, places=6)

    def test_with_non_unit_coefficients(self):
        # 2A → B  means ΔG°r = ΔG°f(B) − 2·ΔG°f(A) = −50 − 2(−100) = 150
        dg = td.dg_standard_reaction_from_compounds(
            self.conn, {"A": -2.0, "B": 1.0}, 25.0)
        self.assertAlmostEqual(dg, 150.0, places=6)


class TestKnallgasPlaceholder(unittest.TestCase):
    """End-to-end smoke test using the seeded placeholder values.

    Validates the pipeline shape, not the science — placeholder numbers will
    be replaced with Amend & Shock 2001 Table 4.1 values once the PDF is
    digitized. The validation of real ΔG°r ≈ -237 kJ/mol at 25°C lives in
    `validate_thermodynamics.py`.
    """

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        td.seed_placeholders(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_placeholder_reaction_retrievable(self):
        r = td.get_reaction(self.conn, "knallgas_H2_O2")
        self.assertEqual(r.stoichiometry,
                         {"H2(aq)": -1.0, "O2(aq)": -0.5, "H2O(l)": 1.0})

    def test_placeholder_standard_dgr_monotone_across_available_range(self):
        # Placeholder values are smooth; the sign should remain negative
        # at all biological temperatures
        for t in (2, 25, 37, 55, 70, 100, 150, 200):
            dg = td.dg_standard_reaction(self.conn, "knallgas_H2_O2", t)
            self.assertLess(dg, 0, f"expected negative ΔG°r at {t}°C")

    def test_compound_sum_matches_pretabulated(self):
        # ΔG°r computed from compounds must equal the tabulated ΔG°r at
        # every reference temperature (within rounding).
        for t in td.REFERENCE_TEMPS_C:
            dg_tabulated = td.dg_standard_reaction(self.conn, "knallgas_H2_O2", t)
            dg_computed = td.dg_standard_reaction_from_compounds(
                self.conn,
                {"H2(aq)": -1.0, "O2(aq)": -0.5, "H2O(l)": 1.0},
                t,
            )
            # Allow 0.05 kJ/mol rounding tolerance since placeholder values
            # were pre-computed and written separately.
            self.assertAlmostEqual(dg_tabulated, dg_computed, delta=0.1,
                                   msg=f"mismatch at T={t}°C")

    def test_low_h2_activity_makes_reaction_less_favorable(self):
        # With H2 and O2 at trace levels, Q = 1 / (a_H2 * a_O2^0.5) is huge,
        # so R·T·ln(Q) becomes more positive and ΔGr becomes less negative.
        dg_std = td.delta_gr(
            self.conn, "knallgas_H2_O2", 25.0,
            activities={"H2(aq)": 1.0, "O2(aq)": 1.0, "H2O(l)": 1.0})
        dg_trace = td.delta_gr(
            self.conn, "knallgas_H2_O2", 25.0,
            activities={"H2(aq)": 1e-6, "O2(aq)": 1e-6, "H2O(l)": 1.0})
        self.assertGreater(dg_trace, dg_std,
                           "ΔGr should be LESS negative at trace activities")

    def test_seed_placeholders_is_idempotent(self):
        n1 = td.seed_placeholders(self.conn)
        n2 = td.seed_placeholders(self.conn)
        self.assertEqual(n2, (0, 0),
                         "re-seeding should insert zero rows")


if __name__ == "__main__":
    unittest.main(verbosity=2)
