from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
from datetime import datetime, timezone, timedelta
import uuid
from dotenv import load_dotenv
from supabase import create_client, Client
import httpx
import uvicorn
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv(override=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()

# Initialize FastAPI app
app = FastAPI(
    title="Clip Booking API",
    description="API for managing clip editing bookings with payment integration",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
easyslip_token = os.getenv("EASYSLIP_TOKEN")
easyslip_url = os.getenv("EASYSLIP_URL")
slip_bucket_name = os.getenv("SLIP_BUCKET_NAME")
time_diff_limit = int(os.getenv("TIME_DIFF_LIMIT"))
amount = int(os.getenv("AMOUNT"))
receiver_name = os.getenv("RECEIVER_NAME")

# Cronjob Configuration
BOOKING_CLEANUP_MINUTES = int(os.getenv("BOOKING_CLEANUP_MINUTES", "10"))
CRON_ENABLED = os.getenv("CRON_ENABLED", "true").lower() == "true"

if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")

supabase: Client = create_client(supabase_url, supabase_key)

# Initialize scheduler for cronjobs
scheduler = AsyncIOScheduler()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic models
class PaymentRequest(BaseModel):
    user_id: str
    display_name: str
    selected_date: str
    amount: float
    qr_code_url: str

class PaymentResponse(BaseModel):
    payment_id: str
    qr_code_url: str
    amount: float

class PaymentStatusResponse(BaseModel):
    payment_id: str
    status: str
    amount: float
    paid_at: Optional[str] = None

class ConfirmBookingRequest(BaseModel):
    payment_id: str

class ConfirmBookingResponse(BaseModel):
    success: bool
    booking_id: str

class Booking(BaseModel):
    booking_id: str
    payment_id: Optional[str] = None
    user_id: str
    display_name: str
    selected_date: str
    amount: float
    status: str
    created_at: str

class Payment(BaseModel):
    payment_id: str
    user_id: str
    display_name: str
    selected_date: str
    amount: float
    status: str
    created_at: str
    qr_code_url: str
    paid_at: Optional[str] = None

class CreateBookingRequest(BaseModel):
    user_id: str
    display_name: str
    selected_date: str
    amount: float
    status: str

# EasySlip API Models
class EasySlipAmount(BaseModel):
    amount: float
    local: Optional[dict] = None

class EasySlipBank(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    short: Optional[str] = None

class EasySlipAccountName(BaseModel):
    th: Optional[str] = None
    en: Optional[str] = None

class EasySlipAccount(BaseModel):
    name: EasySlipAccountName
    bank: Optional[dict] = None
    proxy: Optional[dict] = None

class EasySlipSender(BaseModel):
    bank: EasySlipBank
    account: EasySlipAccount

class EasySlipReceiver(BaseModel):
    bank: EasySlipBank
    account: EasySlipAccount
    merchantId: Optional[str] = None

class EasySlipData(BaseModel):
    payload: str
    transRef: str
    date: str
    countryCode: str
    amount: EasySlipAmount
    fee: Optional[float] = None
    ref1: Optional[str] = None
    ref2: Optional[str] = None
    ref3: Optional[str] = None
    sender: EasySlipSender
    receiver: EasySlipReceiver

class EasySlipResponse(BaseModel):
    status: int
    data: Optional[EasySlipData] = None
    message: Optional[str] = None


async def verify_slip_with_easyslip(file_content: bytes, filename: str) -> EasySlipResponse:
    """Verify slip using EasySlip API"""
    try:
        # Get EasySlip API token from environment
        if not easyslip_token:
            raise Exception("EASYSLIP_TOKEN not configured")
        
        # Prepare the request
        url = easyslip_url
        headers = {
            "Authorization": f"Bearer {easyslip_token}"
        }
        
        # Create form data with checkDuplicate parameter
        files = {
            "file": (filename, file_content, "image/jpeg")
        }
        data = {
            "checkDuplicate": "true"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, files=files, data=data)
            
            if response.status_code == 200:
                # Success response
                response_data = response.json()
                return EasySlipResponse(**response_data)
            else:
                # Error response
                error_data = response.json()
                return EasySlipResponse(
                    status=response.status_code,
                    message=error_data.get("message", "Unknown error")
                )
                
    except Exception as e:
        print(f"Error calling EasySlip API: {e}")
        return EasySlipResponse(
            status=500,
            message="Internal server error"
        )

async def upload_file_to_supabase_storage(file_content: bytes, filename: str, content_type: str, bucket_name: str = slip_bucket_name) -> str:

    try:

        storage_filename = f"slips/{int(datetime.now().timestamp())}_{filename}"
        
        result = supabase.storage.from_(bucket_name).upload(
            path=storage_filename,
            file=file_content,
            file_options={"content-type": content_type}
        )
        
        public_url = supabase.storage.from_(bucket_name).get_public_url(storage_filename)
        print(f"File uploaded successfully: {public_url}")
        return public_url
        
    except Exception as e:
        print(f"Error uploading file: {e}")
        return None

async def cleanup_old_bookings():
    """Clean up pending bookings older than BOOKING_CLEANUP_MINUTES"""
    try:
        logger.info("Starting cleanup of old pending bookings...")
        
        # Calculate cutoff time
        cutoff_time = datetime.now() - timedelta(minutes=BOOKING_CLEANUP_MINUTES)
        
        # Get old pending bookings only
        result = supabase.table("bookings").select("booking_id, created_at, status").lt("created_at", cutoff_time.isoformat()).eq("status", "pending").execute()
        
        if not result.data:
            logger.info("No old pending bookings found to clean up")
            return
        
        # Delete old pending bookings
        deleted_count = 0
        for booking in result.data:
            try:
                supabase.table("bookings").delete().eq("booking_id", booking["booking_id"]).execute()
                deleted_count += 1
                logger.info(f"Deleted old pending booking: {booking['booking_id']}")
            except Exception as e:
                logger.error(f"Error deleting booking {booking['booking_id']}: {e}")
        
        logger.info(f"Cleanup completed. Deleted {deleted_count} old pending bookings")
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_bookings: {e}")

def start_scheduler():
    """Start the cronjob scheduler"""
    if not CRON_ENABLED:
        logger.info("Cronjobs disabled. Set CRON_ENABLED=true to enable.")
        return
    
    try:
        # Add cronjob to run every 5 minutes
        scheduler.add_job(
            cleanup_old_bookings,
            CronTrigger(minute="*/5"),  # Run every 5 minutes
            id="cleanup_old_bookings",
            name="Cleanup Old Bookings",
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("Cronjob scheduler started successfully - running every 5 minutes")
        
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")

def stop_scheduler():
    """Stop the cronjob scheduler"""
    try:
        scheduler.shutdown()
        logger.info("Cronjob scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")

# API Endpoints
@app.post("/generate-payment")
async def generate_payment(
    request: PaymentRequest
):
    try:     
        payment_id = f"payment_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:9]}"

        payment_data = {
            "payment_id": payment_id,
            "user_id": request.user_id,
            "display_name": request.display_name,
            "selected_date": request.selected_date,
            "amount": request.amount,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "qr_code_url": request.qr_code_url
        }
        
        response = supabase.table("payments").insert(payment_data).execute()
        
        return response.data
    
    except Exception as e:
        print(f"Error generating payment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/create-booking")
async def create_booking(
    request: CreateBookingRequest,
):
    """Create a new booking"""
    try:
        booking_id = f"booking_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:9]}"
        booking_data = {
            "booking_id": booking_id,
            "user_id": request.user_id,
            "display_name": request.display_name,
            "selected_date": request.selected_date,
            "amount": request.amount,
            "status": request.status,
        }
        response = supabase.table("bookings").insert(booking_data).execute()
        
        # Return response in camelCase format
        return response.data[0]
    
    except Exception as e:
        error_msg = str(e)
        print(f"Error creating booking: {error_msg}")
        
        if "duplicate key value violates unique constraint" in error_msg:
            raise HTTPException(
                status_code=409, 
                detail="Booking already exists for this date. Please choose a different date."
            )
        else:
            raise HTTPException(status_code=500, detail=error_msg)

@app.get("/bookings", response_model=List[Booking])
async def get_bookings():
    try:
        result = supabase.table("bookings").select("*").execute()
        return result.data
    except Exception as e:
        print(f"Error getting bookings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/payments", response_model=List[Payment])
async def get_payments():
    try:
        result = supabase.table("payments").select("*").execute()
        return result.data
    except Exception as e:
        print(f"Error getting payments: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/verify-slip", response_model=EasySlipResponse)
async def verify_slip(slip_image: UploadFile = File(...)):
    """Verify slip using EasySlip API"""
    try:
        # Validate file type
        if not slip_image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read file content
        file_content = await slip_image.read()
        
        # Call EasySlip API
        result = await verify_slip_with_easyslip(file_content, slip_image.filename)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in verify_slip: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/verify-slip-with-validation")
async def verify_slip_with_validation(
    payment_id: str = Form(...),
    user_id: str = Form(...),
    display_name: str = Form(...),
    selected_date: str = Form(...),
    amount: float = Form(...),
    slip_image: UploadFile = File(...)
):
    """Verify slip with business validation rules and insert new record"""
    try:
        # 1. Validate file type
        if not slip_image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # 2. Read file content and call EasySlip API
        file_content = await slip_image.read()
        easyslip_result = await verify_slip_with_easyslip(file_content, slip_image.filename)
        
        # 3. Upload slip image to Supabase Storage
        slip_url = await upload_file_to_supabase_storage(
            file_content=file_content,
            filename=slip_image.filename,
            content_type=slip_image.content_type
        )
        
        # 3. Check if EasySlip API was successful
        if easyslip_result.status != 200:
            # Insert record with error
            payment_data = {
                "payment_id": payment_id,
                "user_id": user_id,
                "display_name": display_name,
                "selected_date": selected_date,
                "amount": amount,
                "status": "failed",
                "status_code": str(easyslip_result.status),
                "response": easyslip_result.message,
                "metadata": easyslip_result.model_dump(),
                "slip_url": slip_url
            }
            
            supabase.table("payments").insert(payment_data).execute()
            
            return {
                "success": False,
                "message": f"EasySlip API error: {easyslip_result.message}",
                "status_code": easyslip_result.status
            }
        
        # 4. Validate business rules
        validation_errors = []
        
        # Check 2: Date within 10 minutes of current time
        # ใช้เวลาปัจจุบันใน timezone ไทย
        thailand_tz = timezone(timedelta(hours=7))
        current_time = datetime.now(thailand_tz)  # เวลาปัจจุบันใน timezone ไทย
        slip_date = datetime.fromisoformat(easyslip_result.data.date)  # +07:00
        time_diff = abs((slip_date - current_time).total_seconds() / 60)
        
        if time_diff > time_diff_limit:
            validation_errors.append(f"Payment time difference is {time_diff:.1f} minutes, must be within 10 minutes")
        
        if easyslip_result.data.amount.amount != amount:
            validation_errors.append(f"Amount is {easyslip_result.data.amount.amount}, must be {amount}")
        
        receiver_name_th = easyslip_result.data.receiver.account.name.th
        if receiver_name_th != receiver_name:
            validation_errors.append(f"Receiver name is '{receiver_name_th}', must be '{receiver_name}'")
        
        # 5. Prepare payment data for insert
        payment_data = {
            "payment_id": payment_id,
            "user_id": user_id,
            "display_name": display_name,
            "selected_date": selected_date,
            "amount": amount,
            "tran_ref": easyslip_result.data.transRef,
            "slip_url": slip_url,
            "metadata": {
                "easyslip_data": easyslip_result.data.model_dump(),
                "sender_bank": easyslip_result.data.sender.bank.name,
                "sender_name": easyslip_result.data.sender.account.name.th,
                "receiver_name": easyslip_result.data.receiver.account.name.th,
                "transaction_date": easyslip_result.data.date,
                "country_code": easyslip_result.data.countryCode,
                "fee": easyslip_result.data.fee,
                "payload": easyslip_result.data.payload
            }
        }
        
        # 6. Determine result and insert into database
        if validation_errors:
            # Validation failed
            payment_data.update({
                "status": "failed",
                "status_code": "400",
                "response": "; ".join(validation_errors)
            })
            
            supabase.table("payments").insert(payment_data).execute()
            
            return {
                "success": False,
                "message": "Validation failed",
                "errors": validation_errors,
                "status_code": 400,
                "easyslip_data": easyslip_result.data
            }
        else:
            # Validation passed
            payment_data.update({
                "status": "success",
                "status_code": "200",
                "response": "Payment verified successfully",
                "paid_at": easyslip_result.data.date
            })
            
            supabase.table("payments").insert(payment_data).execute()
            
            return {
                "success": True,
                "message": "Payment verified successfully",
                "status_code": 200,
                "easyslip_data": easyslip_result.data
            }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in verify_slip_with_validation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/bookings/{booking_id}")
async def update_booking(
    booking_id: str,
    user_id: str = Form(None),
    display_name: str = Form(None),
    selected_date: str = Form(None),
    amount: float = Form(None),
    status: str = Form(None),
    payment_id: str = Form(None)
):
    """Update a booking by booking_id"""
    try:
        # Check if booking exists
        booking_result = supabase.table("bookings").select("*").eq("booking_id", booking_id).execute()
        
        if not booking_result.data:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Prepare update data - only include fields that are provided
        update_data = {}
        
        if user_id is not None:
            update_data["user_id"] = user_id
        if display_name is not None:
            update_data["display_name"] = display_name
        if selected_date is not None:
            update_data["selected_date"] = selected_date
        if amount is not None:
            update_data["amount"] = amount
        if status is not None:
            update_data["status"] = status
        if payment_id is not None:
            update_data["payment_id"] = payment_id
        
        # Check if there's any data to update
        if not update_data:
            raise HTTPException(status_code=400, detail="No data provided for update")
        
        # Update the booking
        supabase.table("bookings").update(update_data).eq("booking_id", booking_id).execute()
        
        return {
            "success": True,
            "message": "Booking updated successfully",
            "booking_id": booking_id,
            "updated_data": update_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating booking: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/bookings/{booking_id}")
async def delete_booking(booking_id: str):
    """Delete a booking by booking_id"""
    try:
        # Check if booking exists
        booking_result = supabase.table("bookings").select("*").eq("booking_id", booking_id).execute()
        
        if not booking_result.data:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Delete the booking
        supabase.table("bookings").delete().eq("booking_id", booking_id).execute()
        
        return {
            "success": True,
            "message": "Booking deleted successfully",
            "booking_id": booking_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting booking: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "service": "Clip Booking API"
    }

@app.post("/cleanup/old-bookings")
async def manual_cleanup_old_bookings():
    """Manually trigger cleanup of old bookings"""
    try:
        await cleanup_old_bookings()
        return {
            "success": True,
            "message": "Manual cleanup completed",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in manual cleanup: {e}")
        raise HTTPException(status_code=500, detail="Error during cleanup")

@app.get("/cleanup/status")
async def get_cleanup_status():
    """Get cronjob status and configuration"""
    try:
        jobs = []
        for job in scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "scheduler_running": scheduler.running,
            "cron_enabled": CRON_ENABLED,
            "cleanup_minutes": BOOKING_CLEANUP_MINUTES,
            "jobs": jobs,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting cleanup status: {e}")
        raise HTTPException(status_code=500, detail="Error getting status")

@app.post("/cleanup/start")
async def start_cleanup_scheduler():
    """Start the cleanup scheduler"""
    try:
        start_scheduler()
        return {
            "success": True,
            "message": "Cleanup scheduler started",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        raise HTTPException(status_code=500, detail="Error starting scheduler")

@app.post("/cleanup/stop")
async def stop_cleanup_scheduler():
    """Stop the cleanup scheduler"""
    try:
        stop_scheduler()
        return {
            "success": True,
            "message": "Cleanup scheduler stopped",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        raise HTTPException(status_code=500, detail="Error stopping scheduler")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 