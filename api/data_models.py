
from pydantic import BaseModel
from typing import List
from datetime import datetime

class TradeInput(BaseModel):
    side: str
    security_id: int
    quantity: float
    price: float
    accrued_interest: float

class AllocateTradeRequest(BaseModel):
    as_of_date: datetime
    trades: List[TradeInput]

class AllocationResponse(BaseModel):
    allocations: List[dict]
    status: str

class OptimizationPriority(BaseModel):
    metric_name: str
    weight: float

class SetOptimizationPrioritiesRequest(BaseModel):
    priorities: List[OptimizationPriority]

class OptimizationPrioritiesResponse(BaseModel):
    priorities: List[dict]
    status: str
