import math
from crammer.templates.base import CalcParam, CalcProblem, CalcTemplate


class EOQ(CalcTemplate):
    @property
    def name(self):
        return "经济订货批量"

    @property
    def subject(self):
        return "供应链管理"

    @property
    def params(self):
        return [
            CalcParam("年需求量", "D", 500, 5000, "件", 0),
            CalcParam("每次订货成本", "S", 20, 200, "元", 0),
            CalcParam("单位持有成本", "H", 1, 20, "元/件/年", 0),
        ]

    def compute_answer(self, params):
        D = params["D"]
        S = params["S"]
        H = params["H"]
        eoq = math.sqrt(2 * D * S / H)
        eoq_rounded = round(eoq)
        return (
            f"EOQ = sqrt(2 x {D} x {S} / {H})\n"
            f"    = sqrt({2 * D * S} / {H})\n"
            f"    = sqrt({2 * D * S / H:.1f})\n"
            f"    = {eoq:.2f}\n"
            f"    ≈ {eoq_rounded} 件"
        )

    def generate_question(self, params):
        return (
            f"某企业年需求量 {params['D']} 件，"
            f"每次订货成本 {params['S']} 元，"
            f"单位持有成本 {params['H']} 元/件/年。"
            f"求经济订货批量(EOQ)。"
        )


class Newsvendor(CalcTemplate):
    @property
    def name(self):
        return "报童模型"

    @property
    def subject(self):
        return "供应链管理"

    @property
    def params(self):
        return [
            CalcParam("单位售价", "price", 50, 200, "元", 0),
            CalcParam("单位成本", "cost", 20, 100, "元", 0),
            CalcParam("单位残值", "salvage", 5, 30, "元", 0),
            CalcParam("日均需求(均值)", "mu", 50, 200, "件", 0),
            CalcParam("日均需求(标准差)", "sigma", 10, 50, "件", 0),
        ]

    def compute_answer(self, params):
        price = params["price"]
        cost = params["cost"]
        salvage = params["salvage"]
        mu = params["mu"]
        sigma = params["sigma"]

        cu = price - cost
        co = cost - salvage
        critical_ratio = cu / (cu + co)
        return (
            f"缺货成本 Cu = {price} - {cost} = {cu} 元\n"
            f"超储成本 Co = {cost} - {salvage} = {co} 元\n"
            f"临界比率 = Cu / (Cu + Co) = {cu} / ({cu} + {co}) = {critical_ratio:.4f}\n"
            f"最优订货量 = mu + z * sigma = {mu} + z_cr * {sigma}\n"
            f"(z_cr 为累计标准正态分布在 {critical_ratio:.4f} 处的反函数值)"
        )

    def generate_question(self, params):
        return (
            f"某零售商销售季节性商品，单位售价 {params['price']} 元，"
            f"成本 {params['cost']} 元，季末未售出单位残值 {params['salvage']} 元。"
            f"需求服从正态分布 N({params['mu']}, {params['sigma']}^2)。"
            f"求最优订货量（报童模型）。"
        )
