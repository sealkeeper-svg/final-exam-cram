from crammer.templates.base import CalcTemplate, CalcParam


class BreakEvenAnalysis(CalcTemplate):
    @property
    def name(self) -> str:
        return "保本点分析"

    @property
    def subject(self) -> str:
        return "管理会计"

    @property
    def params(self) -> list[CalcParam]:
        return [
            CalcParam(name="单价", key="price", min_val=20, max_val=500, unit="元"),
            CalcParam(name="单位变动成本", key="vc", min_val=5, max_val=250, unit="元"),
            CalcParam(name="固定成本", key="fc", min_val=10000, max_val=500000, unit="元"),
        ]

    def compute_answer(self, params: dict) -> str:
        price = params["price"]
        vc = params["vc"]
        fc = params["fc"]
        cm = price - vc
        be_qty = fc / cm
        be_amount = be_qty * price
        return (
            f"单位边际贡献 = {price} - {vc} = {cm} 元\n"
            f"保本点销售量 = {fc} / {cm} = {be_qty:.0f} 件\n"
            f"保本点销售额 = {be_qty:.0f} × {price} = {be_amount:.0f} 元"
        )

    def generate_question(self, params: dict) -> str:
        return (
            f"某企业生产X产品，单价{params['price']}元，"
            f"单位变动成本{params['vc']}元，"
            f"固定成本{params['fc']}元。"
            f"求：保本点销售量和销售额。"
        )


class TargetProfit(CalcTemplate):
    @property
    def name(self) -> str:
        return "目标利润分析"

    @property
    def subject(self) -> str:
        return "管理会计"

    @property
    def params(self) -> list[CalcParam]:
        return [
            CalcParam(name="单价", key="price", min_val=20, max_val=500, unit="元"),
            CalcParam(name="单位变动成本", key="vc", min_val=5, max_val=250, unit="元"),
            CalcParam(name="固定成本", key="fc", min_val=10000, max_val=500000, unit="元"),
            CalcParam(name="目标利润", key="target_profit", min_val=5000, max_val=200000, unit="元"),
        ]

    def compute_answer(self, params: dict) -> str:
        price = params["price"]
        vc = params["vc"]
        fc = params["fc"]
        target = params["target_profit"]
        cm = price - vc
        qty = (fc + target) / cm
        return (
            f"单位边际贡献 = {price} - {vc} = {cm} 元\n"
            f"实现目标利润的销售量 = ({fc} + {target}) / {cm} = {qty:.0f} 件"
        )

    def generate_question(self, params: dict) -> str:
        return (
            f"某企业生产X产品，单价{params['price']}元，"
            f"单位变动成本{params['vc']}元，"
            f"固定成本{params['fc']}元，"
            f"目标利润{params['target_profit']}元。"
            f"求：实现目标利润的销售量。"
        )


class MaterialPriceVariance(CalcTemplate):
    @property
    def name(self) -> str:
        return "直接材料价格差异"

    @property
    def subject(self) -> str:
        return "管理会计"

    @property
    def params(self) -> list[CalcParam]:
        return [
            CalcParam(name="标准价格", key="standard_price", min_val=5, max_val=50, unit="元/kg"),
            CalcParam(name="实际价格", key="actual_price", min_val=5, max_val=50, unit="元/kg"),
            CalcParam(name="实际用量", key="actual_quantity", min_val=100, max_val=5000, unit="kg"),
        ]

    def compute_answer(self, params: dict) -> str:
        sp = params["standard_price"]
        ap = params["actual_price"]
        aq = params["actual_quantity"]
        variance = (ap - sp) * aq
        direction = "不利差异" if variance > 0 else "有利差异"
        return (
            f"直接材料价格差异 = ({ap} - {sp}) × {aq} = {variance:.0f} 元（{direction}）"
        )

    def generate_question(self, params: dict) -> str:
        return (
            f"标准价格{params['standard_price']}元/kg，"
            f"实际价格{params['actual_price']}元/kg，"
            f"实际用量{params['actual_quantity']}kg。"
            f"求：直接材料价格差异。"
        )
