
from fastapi import FastAPI, HTTPException
import pandas as pd
import sqlite3
from datetime import datetime
from api.data_models import AllocateTradeRequest, AllocationResponse
from src.pb_optimizer import PBOptimizer
from src.data.data_access_layer import DataAccessLayer
from src.data.initialize_data import initialize_mock_data

app = FastAPI(title="Portfolio Optimization API", version="1.0.0")

# Initialize database connection and data access layer
db_conn = sqlite3.connect("portfolio.db", check_same_thread=False)

# Initialize mock data on startup
initialize_mock_data(db_conn)

dao = DataAccessLayer(db_conn)
optimizer = PBOptimizer(dao)

@app.get("/positions", tags=["Data Access"])
async def get_positions(as_of_date: str, portfolio: str = None):
    try:
        # Convert string date to datetime
        date_obj = datetime.fromisoformat(as_of_date)
        
        # Get positions from data access layer
        positions_df = dao.get_positions(date_obj, [portfolio] if portfolio else None)
        
        # Convert DataFrame to list of dictionaries
        positions_list = positions_df.to_dict('records') if not positions_df.empty else []
        
        return {
            "positions": positions_list,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving positions: {str(e)}")

@app.get("/security-coefficients", tags=["Data Access"])
async def get_security_coefficients(as_of_date: str, portfolio: str = None, security_id: int = None):
    try:
        # Convert string date to datetime
        date_obj = datetime.fromisoformat(as_of_date)
        
        # Get security coefficients from data access layer
        coefficients_df = dao.get_security_pb_coefficients(
            date_obj, 
            [portfolio] if portfolio else None,
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

@app.post("/allocate_trade", response_model=AllocationResponse, tags=['Optimization'])
async def allocate_trade(request: AllocateTradeRequest):
    try:
        # Convert Pydantic models to DataFrame for business logic
        trade_data = []
        for trade in request.trades:
            trade_data.append({
                "side": trade.side,
                "security_id": trade.security_id,
                "quantity": trade.quantity,
                "price": trade.price,
                "accrued_interest": trade.accrued_interest
            })
        
        trade_df = pd.DataFrame(trade_data)
        
        # Call business logic
        allocations_df = await optimizer.allocate_trade_list(request.as_of_date, trade_df)
        
        # Convert result back to response format
        allocations_list = allocations_df.to_dict('records') if not allocations_df.empty else []
        
        return AllocationResponse(
            allocations=allocations_list,
            status="success"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing trade allocation: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
