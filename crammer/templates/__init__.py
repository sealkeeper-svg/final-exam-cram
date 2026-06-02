from crammer.templates.base import CalcTemplate
from crammer.templates.management_accounting import (
    BreakEvenAnalysis,
    TargetProfit,
    MaterialPriceVariance,
)
from crammer.templates.supply_chain import EOQ, Newsvendor
from crammer.templates.economics import PriceElasticity

_TEMPLATES = [
    BreakEvenAnalysis(),
    TargetProfit(),
    MaterialPriceVariance(),
    EOQ(),
    Newsvendor(),
    PriceElasticity(),
]


def get_all_templates() -> list[CalcTemplate]:
    return list(_TEMPLATES)


def find_template(subject: str, template_name: str) -> CalcTemplate | None:
    for t in _TEMPLATES:
        if t.subject == subject and t.name == template_name:
            return t
    return None
