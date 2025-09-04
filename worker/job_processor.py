import asyncio
import json
import os
import yaml
from datetime import datetime
from typing import Dict, List, Any
from form_filler import FormFiller

class JobProcessor:
    def __init__(self):
        self.filler = FormFiller()
        self.job_status = "idle"
        self.current_job_id = None
        
    async def initialize(self, headless: bool = True):
        """Initialize the job processor"""
        await self.filler.initialize(headless)
    
    async def close(self):
        """Clean up resources"""
        await self.filler.close()
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"Failed to load config: {str(e)}")
            return {}
    
    async def process_job(self, job_id: str, excel_path: str, website_url: str, 
                         field_mapping: Dict[str, str], 
                         config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a job with given parameters"""
        
        self.current_job_id = job_id
        self.job_status = "running"
        
        job_result = {
            "job_id": job_id,
            "started_at": datetime.now(),
            "status": "running",
            "excel_path": excel_path,
            "website_url": website_url,
            "field_mapping": field_mapping,
            "results": [],
            "summary": {}
        }
        
        try:
            # Set default config values
            if not config:
                config = {}
            
            submit_selector = config.get("submit_selector")
            success_indicators = config.get("success_indicators", [])
            error_indicators = config.get("error_indicators", [])
            delay_between_rows = config.get("delay_between_rows", 2)
            
            print(f"Starting job {job_id}")
            print(f"Excel file: {excel_path}")
            print(f"Website: {website_url}")
            
            # Process the Excel file
            results = await self.filler.process_excel_file(
                excel_path=excel_path,
                website_url=website_url,
                field_mapping=field_mapping,
                submit_selector=submit_selector,
                success_indicators=success_indicators,
                error_indicators=error_indicators,
                delay_between_rows=delay_between_rows
            )
            
            # Update job result
            job_result["results"] = results
            job_result["completed_at"] = datetime.now()
            job_result["status"] = "completed"
            
            # Generate summary
            total_rows = len(results)
            successful_rows = sum(1 for r in results if r["status"] == "success")
            failed_rows = total_rows - successful_rows
            
            job_result["summary"] = {
                "total_rows": total_rows,
                "successful_rows": successful_rows,
                "failed_rows": failed_rows,
                "success_rate": (successful_rows / total_rows * 100) if total_rows > 0 else 0
            }
            
            # Save job results to file
            results_dir = "job_results"
            os.makedirs(results_dir, exist_ok=True)
            results_file = f"{results_dir}/job_{job_id}_results.json"
            
            with open(results_file, 'w') as f:
                json.dump(job_result, f, indent=2, default=str)
            
            job_result["results_file"] = results_file
            
            print(f"\nJob {job_id} completed!")
            print(f"Total rows: {total_rows}")
            print(f"Successful: {successful_rows}")
            print(f"Failed: {failed_rows}")
            print(f"Results saved to: {results_file}")
            
        except Exception as e:
            job_result["status"] = "error"
            job_result["error"] = str(e)
            job_result["completed_at"] = datetime.now()
            print(f"Job {job_id} failed: {str(e)}")
            
        finally:
            self.job_status = "idle"
            self.current_job_id = None
            
        return job_result
    
    async def process_job_with_config_file(self, job_id: str, excel_path: str, 
                                          config_path: str, 
                                          config_key: str = "website_config") -> Dict[str, Any]:
        """Process a job using configuration from YAML file"""
        
        config = self.load_config(config_path)
        if not config or config_key not in config:
            raise ValueError(f"Invalid config file or missing key '{config_key}'")
        
        website_config = config[config_key]
        
        return await self.process_job(
            job_id=job_id,
            excel_path=excel_path,
            website_url=website_config["url"],
            field_mapping=website_config["field_mapping"],
            config=website_config.get("settings", {})
        )
    
    def get_job_status(self) -> Dict[str, Any]:
        """Get current job status"""
        return {
            "status": self.job_status,
            "current_job_id": self.current_job_id,
            "timestamp": datetime.now()
        }

async def main():
    """Example usage"""
    processor = JobProcessor()
    
    try:
        await processor.initialize(headless=False)
        
        # Example: Process job with direct parameters
        result = await processor.process_job(
            job_id="test_job_001",
            excel_path="example_applicants.xlsx",
            website_url="https://example.com/form",
            field_mapping={
                "ApplicantFirstName": "#first_name",
                "ApplicantLastName": "#last_name",
                "Email": "#email"
            },
            config={
                "delay_between_rows": 2,
                "submit_selector": "#submit_btn"
            }
        )
        
        print("Job completed:", result["summary"])
        
    finally:
        await processor.close()

if __name__ == "__main__":
    asyncio.run(main())