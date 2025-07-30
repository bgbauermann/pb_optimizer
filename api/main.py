from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import pandas as pd
import sqlite3
from datetime import datetime
import secrets
from api.data_models import AllocateTradeRequest, AllocationResponse, SetOptimizationPrioritiesRequest, OptimizationPrioritiesResponse
from src.pb_optimizer import PBOptimizer
from src.data.data_access_layer import DataAccessLayer
from src.data.initialize_data import initialize_mock_data

app = FastAPI(title="PB Optimization API", version="1.0.0")
security = HTTPBasic()

# Simple username/password storage (in production, use a secure database)
VALID_USERS = {
    "user": "secret123"
}

def authenticate_user(credentials: HTTPBasicCredentials = Depends(security)):
    """Authenticate user with basic HTTP authentication"""
    username = credentials.username
    password = credentials.password
    
    if username not in VALID_USERS or not secrets.compare_digest(password, VALID_USERS[username]):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return username

# Initialize database connection and data access layer
db_conn = sqlite3.connect("portfolio.db", check_same_thread=False)
# Initialize mock data on startup
initialize_mock_data(db_conn)
dao = DataAccessLayer(db_conn)
optimizer = PBOptimizer(dao)

@app.get("/positions", tags=["Data Access"])
async def get_positions(as_of_date: str = '2024-01-15', current_user: str = Depends(authenticate_user)):
    try:
        # Convert string date to datetime
        date_obj = datetime.fromisoformat(as_of_date)
        
        # Get positions from data access layer
        positions_df = dao.get_positions(date_obj, None)
        
        # Convert DataFrame to list of dictionaries
        positions_list = positions_df.to_dict('records') if not positions_df.empty else []
        
        return {
            "positions": positions_list,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving positions: {str(e)}")

@app.get("/security-coefficients", tags=["Data Access"])
async def get_security_coefficients(as_of_date: str = '2024-01-15', security_id: int = None, current_user: str = Depends(authenticate_user)):
    try:
        # Convert string date to datetime
        date_obj = datetime.fromisoformat(as_of_date)
        
        # Get security coefficients from data access layer
        coefficients_df = dao.get_security_pb_coefficients(
            date_obj, 
            None,
            [security_id] if security_id else None
        )
        
        # Convert DataFrame to list of dictionaries
        coefficients_list = coefficients_df.to_dict('records') if not coefficients_df.empty else []
        
        return {
            "coefficients": coefficients_list,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving security coefficients: {str(e)}")

@app.get("/optimization-priorities", response_model=OptimizationPrioritiesResponse, tags=["Data Access"])
async def get_optimization_priorities(current_user: str = Depends(authenticate_user)):
    try:
        # Get optimization priorities from data access layer
        priorities_df = dao.get_optimization_priorities()
        
        # Convert DataFrame to list of dictionaries
        priorities_list = priorities_df.to_dict('records') if not priorities_df.empty else []
        
        return OptimizationPrioritiesResponse(
            priorities=priorities_list,
            status="success"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving optimization priorities: {str(e)}")

@app.post("/optimization-priorities", response_model=OptimizationPrioritiesResponse, tags=["Data Access"])
async def set_optimization_priorities(request: SetOptimizationPrioritiesRequest, current_user: str = Depends(authenticate_user)):
    try:
        # Convert Pydantic models to DataFrame
        priorities_data = []
        for priority in request.priorities:
            priorities_data.append({
                "metric_name": priority.metric_name,
                "weight": priority.weight
            })
        
        priorities_df = pd.DataFrame(priorities_data)
        
        # Validate that weights sum to 1.0 (optional business rule)
        total_weight = priorities_df['weight'].sum()
        if abs(total_weight - 1.0) > 0.001:  # Allow small floating point errors
            raise HTTPException(status_code=400, detail=f"Weights must sum to 1.0, got {total_weight}")
        
        # Set optimization priorities in data access layer
        dao.set_optimization_priorities(priorities_df)
        
        # Return the updated priorities
        updated_priorities_df = dao.get_optimization_priorities()
        priorities_list = updated_priorities_df.to_dict('records') if not updated_priorities_df.empty else []
        
        return OptimizationPrioritiesResponse(
            priorities=priorities_list,
            status="success"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error setting optimization priorities: {str(e)}")

allocate_trade_example = [{"as_of_date": "2024-01-15T00:00:00",
                          "trades": [{"security_id": 1001, "market_value": 50000},
                                     {"security_id": 1002, "market_value": 10000}
                                     ]}]

@app.post("/allocate_trade", response_model=AllocationResponse, tags=['Optimization'])
async def allocate_trade(request: AllocateTradeRequest = Body(..., examples=allocate_trade_example),
                         current_user: str = Depends(authenticate_user)):
    """
    Allocate trades across prime brokerage accounts.
    
    Example request:
    ```
    {
        "as_of_date": "2024-01-15T00:00:00",
        "trades": [
            {"security_id": 1001, "market_value": 50000},
            {"security_id": 1002, "market_value": 10000}
        ]
    }
    ```
    """
    try:
        # Convert Pydantic models to DataFrame for business logic
        trade_data = []
        for trade in request.trades:
            trade_data.append({
                "security_id": trade.security_id,
                "market_value": trade.market_value
            })
        
        trade_df = pd.DataFrame(trade_data)
        
        # Call business logic
        allocations_df = await optimizer.allocate_trade_list(request.as_of_date, trade_df)
        
        # Convert result back to response format
        allocations_list = [{k: v} for k, v in allocations_df.to_dict('index').items()] if not allocations_df.empty else []
        
        return AllocationResponse(
            allocations=allocations_list,
            status="success"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing trade allocation: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
