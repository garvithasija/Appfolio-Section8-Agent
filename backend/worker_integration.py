import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add worker directory to path to import worker modules
worker_dir = Path(__file__).parent.parent / "worker"
sys.path.append(str(worker_dir))

try:
    from job_processor import JobProcessor
except ImportError:
    print("Worker modules not available. Install requirements: pip install playwright pandas openpyxl pyyaml")
    JobProcessor = None

class WorkerIntegration:
    def __init__(self):
        self.processor = None
        self.jobs_status = {}
        
    async def initialize_worker(self, headless: bool = None):
        """Initialize the Playwright worker"""
        if JobProcessor is None:
            raise RuntimeError("Worker dependencies not installed")
            
        self.processor = JobProcessor()
        await self.processor.initialize(headless)
    
    async def shutdown_worker(self):
        """Shutdown the worker"""
        if self.processor:
            await self.processor.close()
    
    async def start_form_filling_job(self, job_id: str, excel_path: str, 
                                    website_url: str, field_mapping: Dict[str, str],
                                    config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Start a form filling job with dedicated browser instance"""
        
        # Update job status
        self.jobs_status[job_id] = {
            "status": "starting",
            "started_at": datetime.now(),
            "website_url": website_url,
            "excel_path": excel_path
        }
        
        try:
            # Create dedicated processor for this job
            job_processor = JobProcessor()
            await job_processor.initialize(headless=None)  # Auto-detect based on environment
            print(f"✅ Dedicated browser created for job {job_id}")
            
            # Start job in background with dedicated processor
            asyncio.create_task(self._process_job_async_dedicated(job_id, excel_path, website_url, field_mapping, config, job_processor))
            
            return {
                "success": True,
                "message": f"Job {job_id} started successfully with dedicated browser",
                "job_id": job_id
            }
            
        except Exception as e:
            self.jobs_status[job_id]["status"] = "error"
            self.jobs_status[job_id]["error"] = str(e)
            
            return {
                "success": False,
                "message": f"Failed to start job: {str(e)}",
                "job_id": job_id
            }
    
    async def _process_job_async(self, job_id: str, excel_path: str, 
                               website_url: str, field_mapping: Dict[str, str],
                               config: Dict[str, Any] = None):
        """Process job asynchronously"""
        
        try:
            self.jobs_status[job_id]["status"] = "running"
            
            # Process the job
            result = await self.processor.process_job(
                job_id=job_id,
                excel_path=excel_path,
                website_url=website_url,
                field_mapping=field_mapping,
                config=config or {}
            )
            
            # Update job status with results
            self.jobs_status[job_id].update({
                "status": "completed",
                "completed_at": datetime.now(),
                "results": result,
                "summary": result.get("summary", {})
            })
            
        except Exception as e:
            self.jobs_status[job_id].update({
                "status": "error",
                "error": str(e),
                "completed_at": datetime.now()
            })

    async def _process_job_async_dedicated(self, job_id: str, excel_path: str, 
                               website_url: str, field_mapping: Dict[str, str],
                               config: Dict[str, Any] = None, job_processor = None):
        """Process job asynchronously with dedicated browser instance"""
        
        try:
            self.jobs_status[job_id]["status"] = "running"
            
            # Process the job with dedicated processor
            result = await job_processor.process_job(
                job_id=job_id,
                excel_path=excel_path,
                website_url=website_url,
                field_mapping=field_mapping,
                config=config or {}
            )
            
            # Update job status with results
            self.jobs_status[job_id].update({
                "status": "completed",
                "completed_at": datetime.now(),
                "results": result,
                "summary": result.get("summary", {})
            })
            
        except Exception as e:
            self.jobs_status[job_id].update({
                "status": "error",
                "error": str(e),
                "completed_at": datetime.now()
            })
        finally:
            # Clean up dedicated browser
            if job_processor:
                await job_processor.close()
                print(f"✅ Dedicated browser closed for job {job_id}")
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a specific job"""
        return self.jobs_status.get(job_id, {"status": "not_found"})
    
    def get_all_jobs_status(self) -> Dict[str, Any]:
        """Get status of all jobs"""
        return self.jobs_status
    
    async def start_demo_job(self, job_id: str, excel_path: str) -> Dict[str, Any]:
        """Start a demo job with predefined settings"""
        
        # Demo website configuration
        demo_config = {
            "website_url": "https://httpbin.org/forms/post",  # Demo form site
            "field_mapping": {
                "ApplicantFirstName": "input[name='custname']",
                "ApplicantLastName": "input[name='custtel']", 
                "Email": "input[name='custemail']",
            },
            "config": {
                "delay_between_rows": 2,
                "submit_selector": "input[type='submit']"
            }
        }
        
        return await self.start_form_filling_job(
            job_id=job_id,
            excel_path=excel_path,
            website_url=demo_config["website_url"],
            field_mapping=demo_config["field_mapping"],
            config=demo_config["config"]
        )

# Global worker integration instance
worker_integration = WorkerIntegration()

async def initialize_worker_integration(headless: bool = None):  # Auto-detect based on environment
    """Initialize the global worker integration"""
    try:
        await worker_integration.initialize_worker(headless)
        return True
    except Exception as e:
        print(f"Failed to initialize worker: {str(e)}")
        return False

async def shutdown_worker_integration():
    """Shutdown the global worker integration"""
    await worker_integration.shutdown_worker()