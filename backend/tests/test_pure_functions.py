"""Unit tests for the pure helper functions in main.py.

These touch no DB and no network. conftest configures env before import.
"""

import main


# ── _legal_risk_level ──────────────────────────────────────────────────────────

class TestLegalRiskLevel:
    def test_critical_is_high(self):
        # Arrange/Act/Assert: any critical -> HIGH regardless of serious count.
        assert main._legal_risk_level(1, 0) == "HIGH"

    def test_ten_or_more_serious_is_high(self):
        assert main._legal_risk_level(0, 10) == "HIGH"
        assert main._legal_risk_level(0, 25) == "HIGH"

    def test_some_serious_below_ten_is_medium(self):
        assert main._legal_risk_level(0, 1) == "MEDIUM"
        assert main._legal_risk_level(0, 9) == "MEDIUM"

    def test_clean_is_low(self):
        assert main._legal_risk_level(0, 0) == "LOW"


# ── _compute_release_score ─────────────────────────────────────────────────────

class TestComputeReleaseScore:
    def test_no_issues_is_perfect(self):
        assert main._compute_release_score([]) == 100

    def test_accepts_dicts_and_objects(self):
        # dict form
        assert main._compute_release_score([{"severity": "critical"}]) == 75
        # object form (duck-typed .severity)
        class _I:
            severity = "critical"
        assert main._compute_release_score([_I()]) == 75

    def test_critical_penalty_caps_at_75(self):
        # 1 critical = 25 penalty -> 75; 4+ criticals cap penalty at 75 -> floor 25
        assert main._compute_release_score([{"severity": "critical"}]) == 75
        many = [{"severity": "critical"}] * 10
        assert main._compute_release_score(many) == 25  # 100 - min(250,75)

    def test_serious_penalty_caps_at_50(self):
        many = [{"severity": "serious"}] * 100
        assert main._compute_release_score(many) == 50  # 100 - min(500,50)

    def test_unknown_severity_ignored(self):
        assert main._compute_release_score([{"severity": "bogus"}]) == 100

    def test_never_negative(self):
        worst = (
            [{"severity": "critical"}] * 100
            + [{"severity": "serious"}] * 100
            + [{"severity": "moderate"}] * 100
            + [{"severity": "minor"}] * 100
        )
        assert main._compute_release_score(worst) == 0


# ── verification-aware aggregation (incomplete vs confirmed) ───────────────────

class TestConfirmedAggregation:
    def test_needs_manual_does_not_penalize_score(self):
        # A page with only incomplete items (needs_manual) must score a perfect
        # 100 — incomplete findings are not confirmed violations.
        issues = [{"severity": "serious", "verification": "needs_manual"}] * 36
        assert main._compute_release_score(issues) == 100

    def test_severity_counts_exclude_needs_manual(self):
        issues = [
            {"severity": "critical", "verification": "auto"},
            {"severity": "serious", "verification": "needs_manual"},
            {"severity": "serious", "verification": "needs_manual"},
            {"severity": "minor", "verification": "auto"},
        ]
        counts = main._severity_counts(issues)
        assert counts == {"critical": 1, "serious": 0, "moderate": 0, "minor": 1}

    def test_needs_review_count(self):
        issues = [
            {"severity": "critical", "verification": "auto"},
            {"severity": "serious", "verification": "needs_manual"},
            {"severity": "serious", "verification": "needs_manual"},
        ]
        assert main._needs_review_count(issues) == 2

    def test_is_confirmed_defaults_to_auto_when_missing(self):
        # Safety: a record with no verification attr is treated as confirmed.
        assert main._is_confirmed({"severity": "minor"}) is True

        class _I:
            severity = "minor"
        assert main._is_confirmed(_I()) is True

    def test_is_confirmed_object_form(self):
        class _I:
            severity = "serious"
            verification = "needs_manual"
        assert main._is_confirmed(_I()) is False

    def test_legal_risk_low_when_no_confirmed_high(self):
        # 0 confirmed critical/serious -> LOW even with many incomplete items.
        issues = [{"severity": "serious", "verification": "needs_manual"}] * 36
        c = main._severity_counts(issues)
        assert main._legal_risk_level(c["critical"], c["serious"]) == "LOW"


# ── _wcag_sc_from_tag ──────────────────────────────────────────────────────────

class TestWcagScFromTag:
    def test_three_digit_criterion(self):
        assert main._wcag_sc_from_tag("wcag412") == "4.1.2"

    def test_four_digit_criterion(self):
        assert main._wcag_sc_from_tag("wcag1410") == "1.4.10"

    def test_level_tags_return_none(self):
        # 'wcag2aa' / 'wcag21a' are conformance/version tags, not criteria.
        assert main._wcag_sc_from_tag("wcag2aa") is None
        assert main._wcag_sc_from_tag("wcag21a") is None

    def test_non_wcag_tag_returns_none(self):
        assert main._wcag_sc_from_tag("best-practice") is None
        assert main._wcag_sc_from_tag("section508") is None

    def test_too_short_returns_none(self):
        assert main._wcag_sc_from_tag("wcag41") is None


# ── _wcag_level_from_tags ──────────────────────────────────────────────────────

class TestWcagLevelFromTags:
    def test_aa_detected(self):
        assert main._wcag_level_from_tags(["wcag2aa", "wcag412"]) == "AA"
        assert main._wcag_level_from_tags(["wcag21aa"]) == "AA"

    def test_a_detected(self):
        assert main._wcag_level_from_tags(["wcag2a", "wcag111"]) == "A"

    def test_aa_takes_precedence_over_a(self):
        assert main._wcag_level_from_tags(["wcag2a", "wcag2aa"]) == "AA"

    def test_no_level_tag_returns_none(self):
        assert main._wcag_level_from_tags(["wcag412", "best-practice"]) is None
        assert main._wcag_level_from_tags([]) is None


# ── _normalize_selector ────────────────────────────────────────────────────────

class TestNormalizeSelector:
    def test_empty_is_unknown(self):
        assert main._normalize_selector("") == "unknown"
        assert main._normalize_selector(None) == "unknown"

    def test_strips_nth_child_so_variants_group_together(self):
        a = main._normalize_selector("ul > li:nth-child(2)")
        b = main._normalize_selector("ul > li:nth-child(7)")
        assert a == b  # positional index must not split a component

    def test_strips_unique_ids(self):
        a = main._normalize_selector("button#save-42")
        b = main._normalize_selector("button#save-99")
        assert a == b == "button"

    def test_keeps_role_attribute(self):
        sig = main._normalize_selector('div[role="button"]')
        assert "role" in sig

    def test_data_attr_value_stripped_name_kept(self):
        a = main._normalize_selector('[data-test="a"]')
        b = main._normalize_selector('[data-test="b"]')
        assert a == b
        assert "data-test" in a

    def test_iframe_path_takes_last_segment(self):
        # axe joins iframe path with ", " — the last element is the real target.
        sig = main._normalize_selector("iframe#frame-1, button.cta")
        assert "button" in sig

    def test_generic_tag_keeps_parent_for_context(self):
        sig = main._normalize_selector("nav.main > span")
        # bare generic 'span' should retain a parent segment for disambiguation
        assert ">" in sig and "span" in sig


# ── _guess_component_name ──────────────────────────────────────────────────────

class TestGuessComponentName:
    def test_role_wins(self):
        assert main._guess_component_name('[role="navigation"]') == "Navigation"

    def test_input_type(self):
        assert main._guess_component_name("input[type=checkbox]") == "Input (Checkbox)"

    def test_input_default_text(self):
        assert main._guess_component_name("input") == "Input (Text)"

    def test_tag_with_class(self):
        assert main._guess_component_name("button.cta-primary") == "Button (Cta Primary)"

    def test_bare_known_tag(self):
        assert main._guess_component_name("a") == "Link"

    def test_fallback_non_empty(self):
        # An unrecognized signature still produces a non-empty label.
        assert main._guess_component_name(".some-class")
        assert main._guess_component_name("xyz")

    def test_marquee_class_maps_to_human_name(self):
        # Framework-prefixed marquee classes all resolve to "Marquee".
        assert main._guess_component_name("div.v-marquee") == "Marquee"
        assert main._guess_component_name("div.vmarquee") == "Marquee"
        assert main._guess_component_name(".js-marquee__inner") == "Marquee"

    def test_structural_noise_class_falls_back_to_tag(self):
        # "split-inner" carries no semantic meaning -> use the tag label.
        assert main._guess_component_name("div.split-inner") == "Div"
