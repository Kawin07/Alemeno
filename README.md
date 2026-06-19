# AI-Powered Transaction Processing Pipeline

This project provides an asynchronous backend API for processing raw, dirty financial transaction CSV files. It automatically cleans the data, detects anomalies (statistical outliers and currency mismatches), and uses an LLM (Google Gemini) to classify uncategorised transactions and generate a narrative summary.

## Tech Stack
- **API Framework**: FastAPI (Python 3.12)
- **Database**: PostgreSQL 16 (accessed via SQLAlchemy & Alembic)
- **Job Queue**: Celery with Redis broker
- **LLM**: Google Gemini 2.5 Flash
- **Containerisation**: Docker & Docker Compose

## Prerequisites
- Docker and Docker Compose installed
- A Google Gemini API Key. You can get one for free at [Google AI Studio](https://aistudio.google.com/).

## Setup Instructions

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```

2. **Configure Environment Variables**:
   Copy the example environment file and add your Gemini API Key:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and replace `your-gemini-api-key-here` with your actual key.

3. **Boot the System**:
   Start the entire stack (API, Celery worker, Redis, PostgreSQL) with a single command:
   ```bash
   docker compose up -d --build
   ```
   The database migrations will run automatically before the API starts.

## API Documentation

Once running, you can access the automatic Swagger UI documentation at:
http://localhost:8000/docs

### Example `curl` Requests

#### 1. Upload a CSV
```bash
curl -X POST -F "file=@transactions.csv" http://localhost:8000/jobs/upload
```
*Returns a `job_id` which you will use in subsequent requests.*

#### 2. Check Job Status
```bash
curl http://localhost:8000/jobs/<job_id>/status
```

#### 3. Retrieve Full Results
```bash
curl http://localhost:8000/jobs/<job_id>/results
```

#### 4. List All Jobs
```bash
curl http://localhost:8000/jobs
```

## Architecture & Data Flow
1. **Upload**: Client uploads CSV -> FastAPI saves to DB and enqueues Celery task -> Returns `job_id`.
2. **Clean**: Celery worker loads CSV -> Cleans amounts -> Normalises dates -> Uppercases statuses -> Drops duplicates.
3. **Anomaly Detection**: Calculates median per account to flag 3x outliers -> Flags USD usage with domestic merchants.
4. **LLM Classification**: Uncategorised transactions are batched and sent to Gemini to assign categories (Food, Travel, etc.).
5. **LLM Narrative**: Computes aggregates -> Sends to Gemini to generate a human-readable spending summary and risk level.
6. **Store**: Results are persisted to PostgreSQL `transactions` and `job_summaries` tables. Job status updated to `completed`.

## Troubleshooting
- If the worker fails on LLM calls, check your `.env` file to ensure the `GEMINI_API_KEY` is correct.
- If you change database models, you need to run `alembic revision --autogenerate` locally to create a new migration.
