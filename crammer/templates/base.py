import json
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CalcParam:
    name: str
    key: str
    min_val: float
    max_val: float
    unit: str = ""
    decimal: int = 0


@dataclass
class CalcProblem:
    template_name: str
    question_text: str
    answer_text: str
    params: dict
    params_json: str


class CalcTemplate(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def subject(self) -> str:
        ...

    @property
    @abstractmethod
    def params(self) -> list[CalcParam]:
        ...

    @abstractmethod
    def compute_answer(self, params: dict) -> str:
        ...

    @abstractmethod
    def generate_question(self, params: dict) -> str:
        ...

    def generate(self) -> CalcProblem:
        params = {}
        for param in self.params:
            if param.decimal == 0:
                params[param.key] = random.randint(int(param.min_val), int(param.max_val))
            else:
                val = random.uniform(param.min_val, param.max_val)
                params[param.key] = round(val, param.decimal)
        question_text = self.generate_question(params)
        answer_text = self.compute_answer(params)
        return CalcProblem(
            template_name=self.name,
            question_text=question_text,
            answer_text=answer_text,
            params=params,
            params_json=json.dumps(params, ensure_ascii=False),
        )

    def generate_batch(self, n: int = 5) -> list[CalcProblem]:
        return [self.generate() for _ in range(n)]
