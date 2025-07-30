
# Portfolio Optimization API

A FastAPI-based portfolio optimization system that allocates trades across multiple prime brokerage accounts using configurable optimization metrics.

## Features

- **Trade Allocation**: Optimize trade allocation across multiple prime brokerage accounts
- **Configurable Priorities**: Set and manage optimization metric weights
- **Data Access**: Query positions and security coefficients
- **RESTful API**: Full REST API with authentication
- **Mock Data**: Built-in mock data for testing and development

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

## Getting Started

### Prerequisites

- Python 3.12+
- uv package manager (recommended) or pip

### Installation

1. Clone the repository and navigate to the project directory

2. Install dependencies using uv:
```bash
uv sync
```

Or using pip:
```bash
pip install -r requirements.txt
```

### Running the Application

Start the FastAPI development server:
```bash
uvicorn api.main:app --host 0.0.0.0 --port 5000 --reload
```

The API will be available at `http://0.0.0.0:5000`

### Authentication

The API uses HTTP Basic Authentication. Default credentials:
- Username: `user`
- Password: `secret123`

## API Endpoints

### Data Access

- `GET /positions` - Retrieve portfolio positions for a specific date
- `GET /security-coefficients` - Get security coefficients for optimization
- `GET /optimization-priorities` - Get current optimization metric priorities
- `POST /optimization-priorities` - Update optimization metric priorities

### Optimization

- `POST /allocate_trade` - Allocate trades across prime brokerage accounts

### Interactive Documentation

Visit `http://0.0.0.0:5000/docs` for interactive Swagger UI documentation.

## Example Usage

### Setting Optimization Priorities

```python
import requests

# Set optimization priorities
priorities = {
    "priorities": [
        {"metric_name": "risk", "weight": 0.6},
        {"metric_name": "liquidity", "weight": 0.4}
    ]
}

response = requests.post(
    "http://0.0.0.0:5000/optimization-priorities",
    json=priorities,
    auth=("user", "secret123")
)
```

### Allocating Trades

```python
trade_request = {
    "as_of_date": "2024-01-15T00:00:00",
    "trades": [
        {
            "side": "BUY",
            "security_id": 1001,
            "quantity": 100,
            "price": 15.0,
            "accrued_interest": 0.0
        }
    ]
}

response = requests.post(
    "http://0.0.0.0:5000/allocate_trade",
    json=trade_request,
    auth=("user", "secret123")
)
```

## Docker Deployment

### Building the Docker Image

```bash
docker build -t portfolio-optimizer .
```

### Running the Container

```bash
docker run -p 5000:5000 portfolio-optimizer
```

## Development

### Running Tests

The application includes mock data for testing. To run the optimization engine directly:

```bash
python src/pb_optimizer.py
```

### Database

The application uses SQLite for data storage. The database file (`portfolio.db`) is automatically created and populated with mock data on startup.

## Configuration

### Optimization Metrics

The system supports configurable optimization priorities through the `/optimization-priorities` endpoint. Weights must sum to 1.0.

### Mock Data

Sample data includes:
- Portfolio positions across multiple prime brokers
- Security coefficients for optimization metrics
- Default optimization priorities

## Contributing

1. Follow the existing code structure and patterns
2. Ensure all endpoints include proper authentication
3. Add appropriate error handling for new features
4. Update this README when adding new functionality

## License

This project is for educational and demonstration purposes.
