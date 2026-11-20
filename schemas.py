"""Request/response models. Pydantic validates input and generates the OpenAPI spec."""
import datetime as dt

from pydantic import BaseModel, Field, field_validator


class ExpenseIn(BaseModel):
    amount: float = Field(gt=0, description="Amount spent, must be greater than 0")
    category: str = Field(min_length=1, max_length=50, examples=["food"])
    description: str = Field(default="", max_length=200, examples=["Lunch with team"])
    date: dt.date = Field(description="Date of the expense (YYYY-MM-DD)")

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str) -> str:
        value = value.strip().lower()
        if not value:
            raise ValueError("category must not be blank")
        return value


class ExpenseOut(ExpenseIn):
    id: int


class CategorySummary(BaseModel):
    category: str
    total: float
    count: int
class TotalOut(BaseModel):
    total: float
    count: int