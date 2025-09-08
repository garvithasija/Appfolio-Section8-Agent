from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pandas as pd
import json
import uuid
import os
from datetime import datetime
from typing import Dict, List, Optional
from collections import OrderedDict
import asyncio

try:
    from worker_integration import worker_integration, initialize_worker_integration, shutdown_worker_integration
    WORKER_AVAILABLE = True
except ImportError:
    print("Worker integration not available. Form filling will be simulated.")
    WORKER_AVAILABLE = False

app = FastAPI(title="Section 8 Form Filling Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://section8-frontend.onrender.com",
        "https://*.onrender.com"  # Allow any Render subdomain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for MVP
jobs: Dict[str, dict] = {}
job_results: Dict[str, dict] = {}
chat_messages: Dict[str, List[dict]] = {}
running_jobs: set = set()  # Track currently running jobs

class ChatMessage(BaseModel):
    message: str
    job_id: Optional[str] = None

class FormFillingRequest(BaseModel):
    job_id: str
    website_url: str
    field_mapping: Dict[str, str]
    submit_selector: Optional[str] = None

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: str
    created_at: datetime
    total_rows: int
    completed_rows: int
    errors: List[str]

@app.get("/")
async def root():
    return {"message": "Section 8 Form Filling Agent API"}

@app.post("/jobs")
async def create_job(file: UploadFile = File(...)):
    try:
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Save uploaded file
        os.makedirs("uploads", exist_ok=True)
        file_path = f"uploads/{job_id}_{file.filename}"
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Read Excel or CSV file
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
        
        # Validate required columns - check for either applicant data or tenant receipt data
        applicant_columns = ["ApplicantFirstName", "ApplicantLastName", "DOB"]
        tenant_receipt_columns = ["TenantName", "Amount", "ReceiptDate"]
        
        has_applicant_data = all(col in df.columns for col in applicant_columns)
        has_tenant_data = all(col in df.columns for col in tenant_receipt_columns)
        
        if not has_applicant_data and not has_tenant_data:
            raise HTTPException(
                status_code=400, 
                detail=f"File must contain either applicant columns {applicant_columns} or tenant receipt columns {tenant_receipt_columns}"
            )
        
        # No missing columns if we have either valid set
        missing_columns = []
        
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {missing_columns}"
            )
        
        # Store job info
        jobs[job_id] = {
            "id": job_id,
            "filename": file.filename,
            "file_path": file_path,
            "status": "created",
            "created_at": datetime.now(),
            "total_rows": len(df),
            "completed_rows": 0,
            "data": df.to_dict('records'),
            "errors": []
        }
        
        return {
            "job_id": job_id,
            "message": f"Job created successfully. {len(df)} rows uploaded.",
            "preview": df.head().to_dict('records')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": f"{job['completed_rows']}/{job['total_rows']}",
        "created_at": job["created_at"],
        "total_rows": job["total_rows"],
        "completed_rows": job["completed_rows"],
        "errors": job["errors"]
    }

@app.post("/jobs/{job_id}/start")
async def start_job(job_id: str, website_url: str = "https://sairealty.appfolio.com/accounting/tenant_receipts/new", 
                   field_mapping: Dict[str, str] = None):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    # Allow restarting failed or stuck jobs
    if job["status"] in ["error", "completed"]:
        job["status"] = "created"  # Reset status
        job["errors"] = []
        job["completed_rows"] = 0
        if job_id in running_jobs:
            running_jobs.remove(job_id)
    
    # STRICT duplicate prevention for active jobs
    if job_id in running_jobs or job["status"] in ["running", "starting"]:
        raise HTTPException(status_code=409, detail=f"Job {job_id} is already {job['status']}")
    
    if job["status"] != "created":
        raise HTTPException(status_code=409, detail=f"Job {job_id} status is {job['status']}, expected 'created'")
    
    # Add to running jobs IMMEDIATELY
    running_jobs.add(job_id)
    job["status"] = "starting"
    
    # Default field mapping based on website
    if field_mapping is None:
        if "appfolio" in website_url or "sairealty" in website_url:
            # AppFolio tenant receipts field mapping - Based on actual DOM inspection
            # Ordered to fill Amount right after TenantName
            field_mapping = OrderedDict([
                ("TenantName", "#s2id_autogen3, .select2-focusser, .js-payer input[type='text']"),
                ("Amount", "#receivable_payment_amount"),
                ("ReceiptDate", "#receivable_payment_occurred_on"),
                ("Remarks", "#receivable_payment_remarks"), 
                ("Reference", "#receivable_payment_reference"),
                ("CashAccount", "#s2id_autogen1, .select2-focusser"),  # Handled by choose_cash_account()
                ("PaymentType", "#s2id_autogen2, .select2-focusser")   # Handled by choose_payment_type()
            ])
        else:
            # Demo site field mapping
            field_mapping = {
                "ApplicantFirstName": "input[name='custname']",
                "ApplicantLastName": "input[name='custtel']",
                "Email": "input[name='custemail']"
            }
    
    # Start processing in background
    print(f"🚀 Starting job {job_id} with worker_available={WORKER_AVAILABLE}")
    if WORKER_AVAILABLE:
        print(f"📝 Starting worker job: {job_id}, URL: {website_url}")
        asyncio.create_task(process_job_with_worker(job_id, website_url, field_mapping))
    else:
        print(f"📝 Starting simulated job: {job_id}")
        asyncio.create_task(process_job(job_id))
    
    return {"message": f"Job {job_id} started successfully with website: {website_url}"}

@app.post("/jobs/{job_id}/fill-forms")
async def fill_forms(job_id: str, request: FormFillingRequest):
    """Start form filling with specific website and field mapping"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if not WORKER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Form filling worker not available")
    
    job = jobs[job_id]
    job["status"] = "running"
    job["website_url"] = request.website_url
    job["field_mapping"] = request.field_mapping
    
    try:
        # Start worker job
        result = await worker_integration.start_form_filling_job(
            job_id=job_id,
            excel_path=job["file_path"],
            website_url=request.website_url,
            field_mapping=request.field_mapping,
            config={
                "submit_selector": request.submit_selector,
                "delay_between_rows": 3
            }
        )
        
        return result
        
    except Exception as e:
        job["status"] = "error"
        job["errors"].append(f"Failed to start form filling: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_job_with_worker(job_id: str, website_url: str, field_mapping: Dict[str, str]):
    """Process job using the actual Playwright worker"""
    job = jobs[job_id]
    
    try:
        print(f"⚙️ Worker starting for job {job_id}")
        # Start worker job
        result = await worker_integration.start_form_filling_job(
            job_id=job_id,
            excel_path=job["file_path"],
            website_url=website_url,
            field_mapping=field_mapping,
            config={
                "delay_between_rows": 3,
                "headless": True,  # Set to False for debugging
                "submit_selector": "#save_button"  # AppFolio save button
            }
        )
        
        if result["success"]:
            job["status"] = "running"
            print(f"✅ Job {job_id} status updated to 'running'")
            
            # Monitor job progress
            while True:
                worker_status = worker_integration.get_job_status(job_id)
                if worker_status["status"] in ["completed", "error"]:
                    # Update job with final results
                    if worker_status["status"] == "completed":
                        job["status"] = "completed"
                        job["completed_rows"] = worker_status.get("summary", {}).get("successful_rows", 0)
                        # Add any errors from worker results
                        if "results" in worker_status:
                            for result in worker_status["results"]["results"]:
                                if result.get("errors"):
                                    job["errors"].extend(result["errors"])
                    else:
                        job["status"] = "error"
                        job["errors"].append(f"Worker error: {worker_status.get('error', 'Unknown error')}")
                    
                    # Remove from running jobs when complete
                    if job_id in running_jobs:
                        running_jobs.remove(job_id)
                    break
                
                await asyncio.sleep(2)  # Check every 2 seconds
        else:
            job["status"] = "error"
            job["errors"].append(f"Failed to start worker: {result['message']}")
            print(f"❌ Worker failed to start for job {job_id}: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        job["status"] = "error" 
        job["errors"].append(f"Worker integration error: {str(e)}")
        print(f"💥 Exception in worker integration for job {job_id}: {str(e)}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
        # Remove from running jobs on error
        if job_id in running_jobs:
            running_jobs.remove(job_id)

async def process_job(job_id: str):
    """Fallback simulated job processing when worker is not available"""
    job = jobs[job_id]
    data = job["data"]
    
    for i, row in enumerate(data):
        try:
            # Simulate form filling process
            await asyncio.sleep(2)  # Simulate processing time
            
            # For MVP, just simulate success/failure
            success_rate = 0.9  # 90% success rate for demo
            if i % 10 == 0:  # Every 10th row fails for demo
                job["errors"].append(f"Row {i+1}: Simulated error - missing DOB validation")
            else:
                job["completed_rows"] += 1
            
            # Update progress
            job["progress"] = f"{job['completed_rows']}/{job['total_rows']}"
            
        except Exception as e:
            job["errors"].append(f"Row {i+1}: {str(e)}")
    
    job["status"] = "completed"

@app.post("/chat")
async def chat_endpoint(chat_message: ChatMessage):
    message = chat_message.message.lower()
    job_id = chat_message.job_id
    
    # Initialize chat history if needed
    if job_id and job_id not in chat_messages:
        chat_messages[job_id] = []
    
    # Process user message
    response = ""
    
    if "upload" in message or "file" in message:
        response = "Please upload your Excel file using the upload component above. I'll help you process it once uploaded."
    elif "start" in message or "fill" in message or "submit" in message:
        if job_id and job_id in jobs:
            if jobs[job_id]["status"] == "created":
                # Extract website URL if provided in message
                website_url = "https://sairealty.appfolio.com/accounting/tenant_receipts/new"  # Default to AppFolio
                
                # Check for demo site keywords (opposite logic)
                if "demo" in message or "test" in message or "httpbin" in message:
                    website_url = "https://httpbin.org/forms/post"
                elif "appfolio" in message or "sairealty" in message or "tenant" in message:
                    website_url = "https://sairealty.appfolio.com/accounting/tenant_receipts/new"
                elif "website" in message or "url" in message or "http" in message:
                    # Try to extract URL from message
                    words = chat_message.message.split()
                    for word in words:
                        if word.startswith("http"):
                            website_url = word
                            break
                
                # Check job status and prevent duplicates
                current_status = jobs[job_id]["status"]
                
                if current_status in ["running", "starting"]:
                    response = f"Job #{job_id} is already {current_status}. Please wait for it to complete."
                elif current_status == "completed":
                    response = f"Job #{job_id} is already completed. Upload a new file to start another job."
                elif current_status == "error":
                    response = f"Job #{job_id} had errors. You can try starting it again or upload a new file."
                elif current_status == "created":
                    try:
                        # Start the job
                        await start_job(job_id, website_url)
                        response = f"Great! I've started processing Job #{job_id} for AppFolio website {website_url}. I'll fill out forms for all {jobs[job_id]['total_rows']} applicants. You'll see progress updates here."
                    except HTTPException as e:
                        if e.status_code == 409:
                            response = f"Job #{job_id} is already running. Please wait for it to complete."
                        else:
                            response = f"Failed to start job #{job_id}: {e.detail}"
                else:
                    response = f"Job #{job_id} has unexpected status: {current_status}"
            else:
                response = f"Job #{job_id} is already {jobs[job_id]['status']}."
        else:
            response = "Please upload an Excel file first, then I can start filling the forms."
    elif "website" in message and job_id and job_id in jobs:
        response = f"Current job will use demo website. To specify a custom website, say 'start filling forms at https://your-website.com' or use the /fill-forms endpoint with field mappings."
    elif "status" in message or "progress" in message:
        if job_id and job_id in jobs:
            job = jobs[job_id]
            response = f"Job #{job_id} Status: {job['status']}\nProgress: {job['completed_rows']}/{job['total_rows']} completed\nErrors: {len(job['errors'])}"
        else:
            response = "No active job found. Please upload a file first."
    elif "error" in message:
        if job_id and job_id in jobs:
            errors = jobs[job_id]["errors"]
            if errors:
                response = f"Found {len(errors)} errors:\n" + "\n".join(errors[:5])  # Show first 5 errors
            else:
                response = "No errors found in the current job."
        else:
            response = "No active job found."
    else:
        response = "Hi! I'm your Section 8 form filling assistant. Upload an Excel file to get started, then ask me to 'start filling' the applications."
    
    # Store messages
    if job_id:
        chat_messages[job_id].extend([
            {"type": "user", "message": chat_message.message, "timestamp": datetime.now()},
            {"type": "agent", "message": response, "timestamp": datetime.now()}
        ])
    
    return {"response": response}

@app.post("/jobs/{job_id}/reset")
async def reset_job(job_id: str):
    """Reset a stuck or failed job back to created status"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    job["status"] = "created"
    job["errors"] = []
    job["completed_rows"] = 0
    
    # Remove from running jobs
    if job_id in running_jobs:
        running_jobs.remove(job_id)
    
    return {"message": f"Job {job_id} has been reset to 'created' status"}

@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await websocket.accept()
    last_update = {}
    
    try:
        while True:
            # Send periodic updates about job progress only if there's a change
            if job_id in jobs:
                job = jobs[job_id]
                current_update = {
                    "type": "progress",
                    "job_id": job_id,
                    "status": job["status"],
                    "progress": f"{job['completed_rows']}/{job['total_rows']}",
                    "completed_rows": job["completed_rows"],
                    "total_rows": job["total_rows"],
                    "errors": len(job["errors"])
                }
                
                # Only send if something changed or if job is completed/error
                if (current_update != last_update or 
                    job["status"] in ["completed", "error"] or
                    job["status"] == "running"):
                    
                    await websocket.send_text(json.dumps(current_update))
                    last_update = current_update.copy()
                    
                    # Stop sending updates if job is completed or errored
                    if job["status"] in ["completed", "error"]:
                        break
            
            await asyncio.sleep(3)  # Check every 3 seconds instead of 1
            
    except Exception as e:
        print(f"WebSocket error: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize worker integration on startup"""
    if WORKER_AVAILABLE:
        success = await initialize_worker_integration(headless=False)  # Visual mode
        if success:
            print("✅ Worker integration initialized successfully")
        else:
            print("❌ Failed to initialize worker integration")
    else:
        print("⚠️ Worker integration not available - running in simulation mode")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up worker integration on shutdown"""
    if WORKER_AVAILABLE:
        await shutdown_worker_integration()
        print("Worker integration shut down")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)