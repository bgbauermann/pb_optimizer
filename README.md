
# PB Optimization API

A FastAPI-based portfolio optimization system that allocates trades across multiple prime brokerage accounts using configurable optimization metrics.

## Project Structure

```
├── api/                     # FastAPI application
│   ├── data_models.py      # Pydantic models for API requests/responses
│   └── main.py             # FastAPI application and endpoints
├── src/                    # Core business logic
│   ├── data/               # Data access and initialization
│   │   ├── data_access_layer.py    # Database access layer
│   │   ├── initialize_data.py      # Mock data initialization
│   │   └── *.csv                   # Sample data files
│   ├── pb_optimizer.py     # Portfolio optimization engine
│   └── trade.py           # Trade data structures
├── Dockerfile             # Docker containerization
└── pyproject.toml        # Python dependencies
```

