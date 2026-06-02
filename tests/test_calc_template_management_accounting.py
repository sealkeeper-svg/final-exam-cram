import pytest

from crammer.templates.management_accounting import (
    BreakEvenAnalysis,
    TargetProfit,
    MaterialPriceVariance,
)


class TestBreakEvenAnalysis:
    def test_compute_answer(self):
        template = BreakEvenAnalysis()
        params = {"price": 100, "vc": 60, "fc": 20000}
        answer = template.compute_answer(params)
        assert "40" in answer
        assert "500" in answer
        assert "50000" in answer

    def test_generate_question(self):
        template = BreakEvenAnalysis()
        params = {"price": 100, "vc": 60, "fc": 20000}
        question = template.generate_question(params)
        assert "100" in question
        assert "60" in question
        assert "20000" in question


class TestTargetProfit:
    def test_compute_answer(self):
        template = TargetProfit()
        params = {"price": 100, "vc": 60, "fc": 20000, "target_profit": 10000}
        answer = template.compute_answer(params)
        assert "750" in answer

    def test_generate_question(self):
        template = TargetProfit()
        params = {"price": 100, "vc": 60, "fc": 20000, "target_profit": 10000}
        question = template.generate_question(params)
        assert "10000" in question


class TestMaterialPriceVariance:
    def test_compute_answer_unfavorable(self):
        template = MaterialPriceVariance()
        params = {"standard_price": 10, "actual_price": 12, "actual_quantity": 500}
        answer = template.compute_answer(params)
        assert "1000" in answer
        assert "不利" in answer

    def test_compute_answer_favorable(self):
        template = MaterialPriceVariance()
        params = {"standard_price": 15, "actual_price": 12, "actual_quantity": 500}
        answer = template.compute_answer(params)
        assert "1500" in answer
        assert "有利" in answer

    def test_generate_question(self):
        template = MaterialPriceVariance()
        params = {"standard_price": 10, "actual_price": 12, "actual_quantity": 500}
        question = template.generate_question(params)
        assert "10" in question
        assert "12" in question
        assert "500" in question


class TestParamsInRange:
    def test_break_even_params_in_range(self):
        template = BreakEvenAnalysis()
        problem = template.generate()
        for param_def in template.params:
            val = problem.params[param_def.key]
            assert param_def.min_val <= val <= param_def.max_val

    def test_target_profit_params_in_range(self):
        template = TargetProfit()
        problem = template.generate()
        for param_def in template.params:
            val = problem.params[param_def.key]
            assert param_def.min_val <= val <= param_def.max_val

    def test_material_price_variance_params_in_range(self):
        template = MaterialPriceVariance()
        problem = template.generate()
        for param_def in template.params:
            val = problem.params[param_def.key]
            assert param_def.min_val <= val <= param_def.max_val
