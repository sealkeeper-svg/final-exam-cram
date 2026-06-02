from crammer.templates.base import CalcParam, CalcProblem, CalcTemplate


class PriceElasticity(CalcTemplate):
    @property
    def name(self):
        return "需求价格弹性"

    @property
    def subject(self):
        return "经济政策"

    @property
    def params(self):
        return [
            CalcParam("初始价格", "P1", 10, 100, "元", 0),
            CalcParam("变化后价格", "P2", 10, 100, "元", 0),
            CalcParam("初始需求量", "Q1", 100, 1000, "件", 0),
            CalcParam("变化后需求量", "Q2", 50, 800, "件", 0),
        ]

    def compute_answer(self, params):
        P1 = params["P1"]
        P2 = params["P2"]
        Q1 = params["Q1"]
        Q2 = params["Q2"]

        q_change = (Q2 - Q1) / Q1
        p_change = (P2 - P1) / P1
        elasticity = abs(q_change / p_change)

        if elasticity > 1:
            category = "富有弹性 (>1)，降价可增加总收益"
        elif elasticity < 1:
            category = "缺乏弹性 (<1)，提价可增加总收益"
        else:
            category = "单位弹性 (=1)"

        return (
            f"需求量变化率 = ({Q2} - {Q1}) / {Q1} = {q_change:.4f}\n"
            f"价格变化率 = ({P2} - {P1}) / {P1} = {p_change:.4f}\n"
            f"需求价格弹性 = |{q_change:.4f} / {p_change:.4f}| = {elasticity:.4f}\n"
            f"判断：{category}"
        )

    def generate_question(self, params):
        return (
            f"某商品价格从 {params['P1']} 元升至 {params['P2']} 元，"
            f"需求量从 {params['Q1']} 件降至 {params['Q2']} 件。"
            f"求需求价格弹性，并判断是富有弹性还是缺乏弹性。"
        )
