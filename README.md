# Section 8 Form Filling Agent MVP

An end-to-end system for automating Section 8 housing application form filling using Excel data, with a React chat interface and Playwright automation.

## System Overview

- **Frontend**: React TypeScript app with Excel upload and chat interface
- **Backend**: FastAPI with job orchestration and chat agent
- **Worker**: Playwright automation for form filling

## Features

✅ **Excel Upload & Preview** - Drag & drop Excel files with applicant data
✅ **Chat Interface** - Natural language interaction with the automation agent  
✅ **Real-time Progress** - WebSocket updates during form filling
✅ **Flexible Website Support** - Configure any website URL and field mappings
✅ **Error Handling** - Screenshots and detailed error reporting
✅ **Job Management** - Track multiple jobs and their status

## Quick Start

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt
python main.py
```

The backend will run on `http://localhost:8000`

### 2. Frontend Setup

```bash
cd frontend
npm install
npm start
```

The frontend will run on `http://localhost:3000`

### 3. Worker Setup (Optional - for real form filling)

```bash
cd worker
pip install -r requirements.txt
playwright install chromium
```

## Usage

### Basic Workflow

1. **Upload Excel File**
   - Use the drag-and-drop area to upload your Excel file
   - Required columns: `ApplicantFirstName`, `ApplicantLastName`, `DOB`
   - Preview shows first 5 rows

2. **Start Chat**
   - Chat with the agent: "Start filling applications"
   - Agent will process all rows in your Excel file
   - Real-time updates show progress

3. **Monitor Progress**
   - View job status in the upload section
   - Chat shows row-by-row progress
   - Screenshots saved for errors

### Advanced Usage

#### Custom Website and Field Mapping

Use the `/jobs/{job_id}/fill-forms` endpoint to specify:

```json
{
  "job_id": "your-job-id",
  "website_url": "https://your-portal.com/application",
  "field_mapping": {
    "ApplicantFirstName": "#first_name_field",
    "ApplicantLastName": "#last_name_field", 
    "DOB": "#birth_date",
    "Email": "#email_address"
  },
  "submit_selector": "#submit_button"
}
```

#### Chat Commands

- `"Start filling applications"` - Begin form filling with demo site
- `"Start filling at https://example.com"` - Use custom website URL  
- `"Show current status"` - Get job progress
- `"Show errors"` - View error details

## Configuration

### Worker Configuration (worker/config_example.yaml)

```yaml
website_config:
  url: "https://your-portal.com/application"
  field_mapping:
    ApplicantFirstName: "#first_name"
    ApplicantLastName: "#last_name"
    DOB: "#date_of_birth"
    Email: "#email"
  submit_selector: "#submit_application"
  settings:
    delay_between_rows: 3
    headless: true
```

### Excel File Format

| ApplicantFirstName | ApplicantLastName | DOB | Email | Phone | Address |
|--------------------|-------------------|-----|-------|-------|---------|
| John | Smith | 1985-03-15 | john@email.com | 555-0101 | 123 Main St |
| Jane | Doe | 1990-07-22 | jane@email.com | 555-0102 | 456 Oak Ave |

## API Endpoints

- `POST /jobs` - Upload Excel file and create job
- `GET /jobs/{id}/status` - Get job status  
- `POST /jobs/{id}/start` - Start job with demo settings
- `POST /jobs/{id}/fill-forms` - Start with custom website/mapping
- `POST /chat` - Send chat messages
- `WS /ws/{job_id}` - Real-time progress updates

## Architecture

```
[React Frontend] ←→ [FastAPI Backend] ←→ [Playwright Worker]
     ↓                      ↓                    ↓
 Chat Interface         Job Management      Form Automation
 Excel Upload          WebSocket Events     Screenshot Capture
 Status Display        Progress Tracking    Error Handling
```

## Troubleshooting

**Backend Issues**:
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check if ports 8000/3000 are available
- Worker requires `playwright install chromium`

**Frontend Issues**:
- Run `npm install` to install dependencies
- Check CORS settings if API calls fail
- Verify backend is running on port 8000

**Worker Issues**:
- Install Playwright browsers: `playwright install`
- For debugging, set `headless: false` in config
- Check CSS selectors match target website structure

## Development

### Running in Development Mode

1. Backend: `uvicorn main:app --reload`
2. Frontend: `npm start` 
3. Worker: Set `headless=False` for visual debugging

### Testing

- Demo website: `https://httpbin.org/forms/post`
- Sample Excel file provided in `/worker/example_applicants.xlsx`
- Use browser dev tools to inspect form selectors

## Production Deployment

1. Set `headless=True` in worker config
2. Configure proper CORS origins
3. Use production WSGI server (gunicorn)
4. Set up proper logging and monitoring
5. Secure file upload directory

## Support

This is an MVP implementation. For production use:
- Add authentication and authorization
- Implement proper error recovery
- Add CAPTCHA handling capabilities
- Set up monitoring and logging
- Consider rate limiting and queue management