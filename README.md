# PDF Processing API with LLM & GitHub Integration

A FastAPI-based service that processes PDF documents, extracts GitHub organization information using LLM, and fetches organization member data.

## Features

- PDF document upload and processing
- LLM-based GitHub organization extraction
- GitHub API integration for member data
- SQLite persistence
- Async processing with job status tracking

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with the following variables:
   ```
   HUGGINGFACE_API_KEY=your_key_here
   GITHUB_TOKEN=your_github_token  # Optional for higher rate limits
   ```

## Running the API

Development:
```bash
uvicorn app.main:app --reload
```

Production:
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## API Endpoints

### POST /api/documents/upload
Upload a PDF document for processing.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: PDF file

**Response:**
```json
{
    "job_id": "unique-job-id",
    "status": "processing"
}
```

### GET /api/jobs/{job_id}
Get the status and results of a processing job.

**Response:**
```json
{
    "job_id": "unique-job-id",
    "status": "completed",
    "original_filename": "document.pdf",
    "extracted_company_username": "github-org",
    "github_members": ["member1", "member2"],
    "timestamp": "2024-02-28T12:00:00Z"
}
```

## Error Handling

The API implements proper error handling for:
- Invalid PDF files
- LLM API rate limits and failures
- GitHub API errors
- Database connection issues

## Database Schema

```sql
CREATE TABLE jobs (
    job_id TEXT PRIMARY KEY,
    original_filename TEXT NOT NULL,
    extracted_company_username TEXT,
    github_members TEXT,
    status TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
``` 