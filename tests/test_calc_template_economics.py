from crammer.templates.economics import PriceElasticity


def test_elasticity_calculation():
    t = PriceElasticity()
    prob = t.generate()
    assert prob.template_name == "需求价格弹性"
    assert "弹性" in prob.answer_text
    assert "富有弹性" in prob.answer_text or "缺乏弹性" in prob.answer_text or "单位弹性" in prob.answer_text
    assert isinstance(prob.params["P1"], (int, float))
    assert isinstance(prob.params["Q1"], (int, float))


def test_elasticity_deterministic():
    import random
    random.seed(42)
    t = PriceElasticity()
    prob = t.generate()
    Q1 = prob.params["Q1"]
    Q2 = prob.params["Q2"]
    P1 = prob.params["P1"]
    P2 = prob.params["P2"]
    q_change = (Q2 - Q1) / Q1
    p_change = (P2 - P1) / P1
    expected = abs(q_change / p_change)
    assert f"{expected:.4f}" in prob.answer_text
