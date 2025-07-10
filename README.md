# PDF Processing API - Async Queue

A FastAPI-based service that processes PDF documents asynchronously using a background task queue to extract GitHub organization information.

## Features

- **Async PDF Processing**: Non-blocking upload with background queue processing
- **Task Queue System**: Built-in asyncio queue for handling multiple requests
- **Real-time Status Tracking**: Monitor job progress through different states
- **Simulated Long Processing**: 30-300 second delays to simulate real-world processing
- **GitHub API Integration**: Fetch organization member data
- **SQLite Persistence**: Job status and results storage
- **Clean Architecture**: Simple, maintainable codebase

## How It Works

1. **Immediate Response**: Upload endpoint returns immediately with job ID
2. **Background Processing**: Tasks are queued and processed asynchronously
3. **Status Tracking**: Jobs progress through states: `queued` → `processing` → `completed`/`failed`
4. **Non-blocking**: Multiple uploads can be handled simultaneously

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
Upload a PDF document for async processing.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: PDF file

**Response (Immediate):**
```json
{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "queued",
    "message": "PDF uploaded successfully. Processing will begin shortly.",
    "estimated_processing_time": "30-300 seconds"
}
```

### GET /api/jobs/{job_id}
Get job status and results.

**Possible Statuses:**
- `queued`: Job is waiting in queue
- `processing`: Job is currently being processed
- `completed`: Job finished successfully
- `failed`: Job encountered an error

**Response Examples:**

*Queued:*
```json
{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "original_filename": "document.pdf",
    "extracted_company_username": null,
    "github_members": null,
    "status": "queued",
    "timestamp": "2024-02-28T12:00:00",
    "message": "Job is waiting in queue to be processed"
}
```

*Completed:*
```json
{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "original_filename": "document.pdf",
    "extracted_company_username": "openai",
    "github_members": ["member1", "member2", "member3"],
    "status": "completed",
    "timestamp": "2024-02-28T12:00:00",
    "message": "Job completed successfully"
}
```

### GET /api/queue/status
Get current queue statistics and system status.

**Response:**
```json
{
    "worker_running": true,
    "queue_size": 3,
    "job_statistics": {
        "queued": 2,
        "processing": 1,
        "completed": 15,
        "failed": 1
    },
    "total_jobs": 19
}
```

## Project Structure

```
├── main.py              # FastAPI application with async endpoints
├── task_queue.py        # Async task queue system and worker
├── pdf_processor.py     # PDF processing logic
├── requirements.txt     # Dependencies
├── README.md           # This file
├── test_document.txt   # Sample test file
└── uploads/            # Temporary file storage (auto-created)
```

## Technical Implementation

### Queue System
- **AsyncIO Queue**: Built-in Python asyncio.Queue for task management
- **Background Worker**: Dedicated async worker processes tasks continuously
- **Automatic Cleanup**: Files are deleted after processing
- **Error Recovery**: Failed jobs are marked appropriately

### Processing Flow
1. **Upload**: File saved, job created with "queued" status
2. **Queue**: Task added to asyncio queue
3. **Processing**: Worker picks up task, updates status to "processing"
4. **Simulation**: 30-300 second delay simulates long processing
5. **Completion**: Results saved, status updated to "completed"/"failed"
6. **Cleanup**: Temporary files removed

### Simulated Processing Time
- **Random Delay**: Each job takes 30-300 seconds to complete
- **Real Processing**: Actual PDF text extraction and GitHub API calls
- **Status Updates**: Real-time status changes during processing

## Testing

1. **Upload Multiple PDFs**: Test concurrent processing
   ```bash
   curl -X POST "http://localhost:8000/api/documents/upload" \
        -H "Content-Type: multipart/form-data" \
        -F "file=@test_document.pdf"
   ```

2. **Check Status**: Monitor job progress
   ```bash
   curl "http://localhost:8000/api/jobs/{job_id}"
   ```

3. **Queue Status**: Monitor system health
   ```bash
   curl "http://localhost:8000/api/queue/status"
   ```

## Performance Characteristics

- **Non-blocking Uploads**: Immediate response regardless of queue size
- **Concurrent Processing**: Single background worker processes tasks sequentially
- **Memory Efficient**: Files processed one at a time
- **Scalable Design**: Easy to extend with multiple workers or distributed queues

## Error Handling

- **Upload Failures**: Immediate HTTP error responses
- **Processing Failures**: Jobs marked as "failed" with cleanup
- **Worker Recovery**: Continues processing despite individual task failures
- **Resource Management**: Automatic file cleanup in all scenarios 