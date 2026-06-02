from crammer.templates.supply_chain import EOQ, Newsvendor


def test_eoq_calculation():
    t = EOQ()
    prob = t.generate()
    assert prob.template_name == "经济订货批量"
    assert "EOQ" in prob.answer_text or "sqrt" in prob.answer_text.lower() or "√" in prob.answer_text
    assert isinstance(prob.params["D"], (int, float))
    assert isinstance(prob.params["S"], (int, float))
    assert isinstance(prob.params["H"], (int, float))


def test_eoq_deterministic():
    import random
    random.seed(42)
    t = EOQ()
    prob = t.generate()
    D = prob.params["D"]
    S = prob.params["S"]
    H = prob.params["H"]
    import math
    expected = round(math.sqrt(2 * D * S / H))
    assert str(expected) in prob.answer_text or f"≈ {expected}" in prob.answer_text


def test_newsvendor():
    t = Newsvendor()
    prob = t.generate()
    assert prob.template_name == "报童模型"
    assert "Cu" in prob.answer_text
    assert "Co" in prob.answer_text
