# Energy Optimization AI Agent

## Overview
The AI Agent is a FastAPI application that processes natural language queries about energy data, translating them into SQL queries. It provides an intuitive interface for users to ask questions about energy consumption in plain language and receive structured responses.

## Technology Stack
- FastAPI: Web framework for API endpoints
- Python: Programming language
- Langchain: Framework for LLM-powered applications
- Google Generative AI: LLM provider for natural language processing
- SQLAlchemy & Psycopg2: Database connectivity
- Docker: Containerization for deployment

## Project Structure
```
energy-ai-agent/
├── app/
│   ├── api/
│   │   ├── endpoints.py         # API route definitions
│   │   └── models.py            # Pydantic models for requests/responses
│   ├── core/
│   │   ├── config.py            # Application configuration
│   │   └── security.py          # Security utilities
│   ├── services/
│   │   ├── database.py          # Database connection management
│   │   ├── llm.py               # LLM interaction services
│   │   └── query_processor.py   # Natural language to SQL processing
│   ├── utils/
│   │   └── helpers.py           # Utility functions
│   └── main.py                  # FastAPI application entry point
├── tests/                       # Test cases
├── Dockerfile                   # Docker configuration
└── requirements.txt             # Python dependencies
```

## Features
- Natural language processing of energy-related queries
- Secure database access with house-specific constraints
- API key authentication for service-to-service communication
- Direct SQL query support for advanced users

## Environment Variables
The following environment variables need to be configured:
```
GOOGLE_API_KEY=your_google_api_key  # API key for Google Generative AI
DB_USER=your_db_username            # Database username
DB_PASSWORD=your_db_password        # Database password
DB_HOST=your_db_host                # Database host address
DB_NAME=your_db_name                # Database name
```

## Usage Examples

```json
# Example 1: Simple Natural Language Query
POST /ask
{
  "query": "What was the average energy consumption for last month?"
}

# Example 2: House-Specific Query
POST /ask
{
  "query": "Show me the peak energy usage times",
  "house_id": "house123"
}

```

## Security
The AI agent implements a strong security model to ensure data access restrictions:
- House ID constraints enforce that queries only return data for authorized houses
- Security filters are explicitly applied to all generated SQL

## Deployment
The application is containerized using Docker and can be deployed to cloud services such as Render.
Configure the application using the environment variables listed above for database connection, API keys, and LLM provider credentials.
