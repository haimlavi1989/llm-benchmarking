# Model Catalog Backend

A Python backend service for managing ML model catalogs, built with FastAPI and following clean architecture principles.

## Project Structure

```
model-catalog-backend/
├── src/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── routes/
│   │   │   └── responses/
│   │   ├── middleware/
│   │   └── dependencies/
│   ├── core/
│   ├── models/
│   ├── repositories/
│   ├── services/
│   ├── schemas/
│   └── utils/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docs/
├── scripts/
│   ├── db/
│   └── deployment/
└── configs/
    ├── kubernetes/
    ├── helm/
    └── docker/
```

## Features

- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy** - SQL toolkit and ORM
- **PostgreSQL** - Primary database
- **Pydantic** - Data validation using Python type annotations
- **Alembic** - Database migration tool
- **Docker** - Containerization support
- **Testing** - Comprehensive test suite with pytest
- **Code Quality** - Black, isort, flake8, and mypy for code formatting and linting

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL
- Docker (optional)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd model-catalog-backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp env.example .env
# Edit .env with your configuration
```

5. Run the application:
```bash
python main.py
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

### Using Docker

1. Build and run with Docker Compose:
```bash
docker-compose up --build
```

This will start both the application and PostgreSQL database.

## Development

### Code Quality

The project uses several tools to maintain code quality:

- **Black** - Code formatting
- **isort** - Import sorting
- **flake8** - Linting
- **mypy** - Type checking

Run all quality checks:
```bash
black src tests
isort src tests
flake8 src tests
mypy src
```

### Testing

Run tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=src --cov-report=html
```

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

## API Documentation

Once the application is running, you can access:

- **Interactive API docs**: `http://localhost:8000/docs`
- **ReDoc documentation**: `http://localhost:8000/redoc`
- **OpenAPI schema**: `http://localhost:8000/openapi.json`

## Architecture

This project follows clean architecture principles with clear separation of concerns:

- **API Layer** (`src/api/`) - Handles HTTP requests and responses
- **Core Layer** (`src/core/`) - Business logic and configuration
- **Models Layer** (`src/models/`) - Database models and ORM definitions
- **Repositories Layer** (`src/repositories/`) - Data access abstraction
- **Services Layer** (`src/services/`) - Business logic implementation
- **Schemas Layer** (`src/schemas/`) - Request/response validation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
