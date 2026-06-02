import random

import pytest

from crammer.templates.base import CalcTemplate, CalcParam, CalcProblem


class _SimpleTemplate(CalcTemplate):
    @property
    def name(self) -> str:
        return "简单加法题"

    @property
    def subject(self) -> str:
        return "数学"

    @property
    def params(self) -> list[CalcParam]:
        return [
            CalcParam(name="加数A", key="a", min_val=1, max_val=100, decimal=0),
            CalcParam(name="加数B", key="b", min_val=1, max_val=100, decimal=0),
        ]

    def compute_answer(self, params: dict) -> str:
        a = params["a"]
        b = params["b"]
        return f"{a} + {b} = {a + b}"

    def generate_question(self, params: dict) -> str:
        return f"计算: {params['a']} + {params['b']} = ?"


class TestCalcTemplateGenerate:
    def test_generate_returns_calc_problem(self):
        template = _SimpleTemplate()
        problem = template.generate()
        assert isinstance(problem, CalcProblem)
        assert problem.template_name == "简单加法题"
        assert "a" in problem.params
        assert "b" in problem.params
        assert isinstance(problem.params["a"], int)
        assert isinstance(problem.params["b"], int)

    def test_generate_batch(self):
        template = _SimpleTemplate()
        problems = template.generate_batch(5)
        assert len(problems) == 5
        param_sets = [p.params_json for p in problems]
        unique = set(param_sets)
        assert len(unique) >= 3

    def test_generate_deterministic(self):
        random.seed(42)
        template = _SimpleTemplate()
        p1 = template.generate()
        random.seed(42)
        p2 = template.generate()
        assert p1.params == p2.params
        assert p1.question_text == p2.question_text
        assert p1.answer_text == p2.answer_text
