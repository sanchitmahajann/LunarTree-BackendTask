# PDF Processing API - Simplified

A simple FastAPI-based service that processes PDF documents and extracts GitHub organization information.

## Features

- PDF document upload and processing
- Regex-based GitHub organization extraction
- GitHub API integration for member data
- SQLite persistence
- Simple, clean architecture

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

## Running the API

Development:
```bash
uvicorn main:app --reload
```

Production:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
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
    "status": "completed"
}
```

### GET /api/jobs/{job_id}
Get the results of a processing job.

**Response:**
```json
{
    "job_id": "unique-job-id",
    "original_filename": "document.pdf",
    "extracted_company_username": "github-org",
    "github_members": ["member1", "member2"],
    "status": "completed",
    "timestamp": "2024-02-28T12:00:00"
}
```

## Project Structure

```
├── main.py              # Main FastAPI application
├── pdf_processor.py     # PDF processing logic
├── requirements.txt     # Dependencies
├── README.md           # This file
├── test_document.txt   # Sample test file
└── uploads/            # Temporary file storage (auto-created)
```

## How it works

1. **PDF Upload**: Upload a PDF via the `/api/documents/upload` endpoint
2. **Text Extraction**: Extract text from PDF using pdfplumber
3. **Organization Detection**: Use regex patterns to find GitHub organization mentions
4. **Member Fetching**: Call GitHub API to get public organization members
5. **Storage**: Save results in SQLite database
6. **Response**: Return job ID and results

## Testing

1. Create a test PDF with text mentioning a GitHub organization (e.g., "Check out github.com/openai")
2. Upload via the API docs at http://localhost:8000/docs
3. Check the results using the job ID

## Error Handling

The API handles:
- Invalid PDF files
- GitHub API errors (404, rate limits)
- File processing errors
- Database connection issues 