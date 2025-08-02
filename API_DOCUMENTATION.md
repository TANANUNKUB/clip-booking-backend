# Clip Booking API Documentation

## Overview

API สำหรับจัดการการจอง clip editing พร้อมระบบ payment integration และ EasySlip verification

## Base URL

```
http://localhost:8000
```

## Authentication

API นี้ไม่ต้องการ authentication สำหรับ endpoints ส่วนใหญ่

## Endpoints

### 1. Health Check

#### `GET /health`

ตรวจสอบสถานะของ API

**Response:**
```json
{
  "status": "OK",
  "timestamp": "2024-01-15T10:30:00",
  "service": "Clip Booking API"
}
```

### 2. Booking Management

#### `GET /bookings`

ดึงรายการการจองทั้งหมด

**Response:**
```json
[
  {
    "booking_id": "booking_1234567890_abc123def",
    "payment_id": "payment_1234567890_xyz789ghi",
    "user_id": "user123",
    "display_name": "John Doe",
    "selected_date": "2024-01-20",
    "amount": 200.0,
    "status": "confirmed",
    "created_at": "2024-01-15T10:30:00"
  }
]
```

#### `GET /bookings/user/{user_id}`

ดึงการจองของ user เฉพาะ

**Parameters:**
- `user_id` (string): ID ของ user

**Response:**
```json
[
  {
    "booking_id": "booking_1234567890_abc123def",
    "payment_id": "payment_1234567890_xyz789ghi",
    "user_id": "user123",
    "display_name": "John Doe",
    "selected_date": "2024-01-20",
    "amount": 200.0,
    "status": "confirmed",
    "created_at": "2024-01-15T10:30:00"
  }
]
```

#### `GET /bookings/user/{user_id}/pending`

ดึงการจองที่ยังเป็น pending ของ user

**Parameters:**
- `user_id` (string): ID ของ user

**Response:**
```json
[
  {
    "booking_id": "booking_1234567890_abc123def",
    "payment_id": null,
    "user_id": "user123",
    "display_name": "John Doe",
    "selected_date": "2024-01-20",
    "amount": 200.0,
    "status": "pending",
    "created_at": "2024-01-15T10:30:00"
  }
]
```

#### `GET /bookings/user/{user_id}/confirmed`

ดึงการจองที่ confirmed แล้วของ user

**Parameters:**
- `user_id` (string): ID ของ user

**Response:**
```json
[
  {
    "booking_id": "booking_1234567890_abc123def",
    "payment_id": "payment_1234567890_xyz789ghi",
    "user_id": "user123",
    "display_name": "John Doe",
    "selected_date": "2024-01-20",
    "amount": 200.0,
    "status": "confirmed",
    "created_at": "2024-01-15T10:30:00"
  }
]
```

#### `POST /create-booking`

สร้างการจองใหม่

**Request Body:**
```json
{
  "user_id": "user123",
  "display_name": "John Doe",
  "selected_date": "2024-01-20",
  "amount": 200.0,
  "status": "pending"
}
```

**Response:**
```json
{
  "booking_id": "booking_1234567890_abc123def",
  "user_id": "user123",
  "display_name": "John Doe",
  "selected_date": "2024-01-20",
  "amount": 200.0,
  "status": "pending"
}
```

#### `PUT /bookings/{booking_id}`

อัปเดตการจอง

**Parameters:**
- `booking_id` (string): ID ของการจอง

**Form Data (all optional):**
- `user_id` (string)
- `display_name` (string)
- `selected_date` (string)
- `amount` (float)
- `status` (string)
- `payment_id` (string)

**Response:**
```json
{
  "success": true,
  "message": "Booking updated successfully",
  "booking_id": "booking_1234567890_abc123def",
  "updated_data": {
    "status": "confirmed"
  }
}
```

#### `DELETE /bookings/{booking_id}`

ลบการจอง

**Parameters:**
- `booking_id` (string): ID ของการจอง

**Response:**
```json
{
  "success": true,
  "message": "Booking deleted successfully",
  "booking_id": "booking_1234567890_abc123def"
}
```

### 3. Payment Management

#### `GET /payments`

ดึงรายการ payment ทั้งหมด

**Response:**
```json
[
  {
    "payment_id": "payment_1234567890_xyz789ghi",
    "user_id": "user123",
    "display_name": "John Doe",
    "selected_date": "2024-01-20",
    "amount": 200.0,
    "status": "success",
    "created_at": "2024-01-15T10:30:00",
    "qr_code_url": "https://example.com/qr.png",
    "paid_at": "2024-01-15T10:35:00"
  }
]
```

#### `POST /generate-payment`

สร้าง payment ใหม่

**Request Body:**
```json
{
  "user_id": "user123",
  "display_name": "John Doe",
  "selected_date": "2024-01-20",
  "amount": 200.0,
  "qr_code_url": "https://example.com/qr.png"
}
```

**Response:**
```json
{
  "payment_id": "payment_1234567890_xyz789ghi",
  "user_id": "user123",
  "display_name": "John Doe",
  "selected_date": "2024-01-20",
  "amount": 200.0,
  "status": "pending",
  "created_at": "2024-01-15T10:30:00",
  "qr_code_url": "https://example.com/qr.png"
}
```

### 4. Slip Verification

#### `POST /verify-slip`

ตรวจสอบ slip ด้วย EasySlip API

**Form Data:**
- `slip_image` (file): ไฟล์รูปภาพ slip

**Response:**
```json
{
  "status": 200,
  "data": {
    "payload": "0038000600000101030060217A4fa65d187c1549805102TH9104FCAF",
    "transRef": "A4fa65d187c154980",
    "date": "2025-07-27T01:40:38+07:00",
    "countryCode": "TH",
    "amount": {
      "amount": 200,
      "local": {
        "amount": 0,
        "currency": ""
      }
    },
    "fee": 0,
    "sender": {
      "bank": {
        "id": "006",
        "name": "ธนาคารกรุงไทย",
        "short": "KTB"
      },
      "account": {
        "name": {
          "th": "นายธนานันต์ เ",
          "en": "MR.Tananun H"
        }
      }
    },
    "receiver": {
      "account": {
        "name": {
          "th": "น.ส. พรปวีณ์ ส",
          "en": "MS. Ponprawee S"
        }
      }
    }
  }
}
```

#### `POST /verify-slip-with-validation`

ตรวจสอบ slip พร้อม business validation

**Form Data:**
- `payment_id` (string): ID ของ payment
- `user_id` (string): ID ของ user
- `display_name` (string): ชื่อที่แสดง
- `selected_date` (string): วันที่เลือก
- `amount` (float): จำนวนเงิน
- `slip_image` (file): ไฟล์รูปภาพ slip

**Response (Success):**
```json
{
  "success": true,
  "message": "Payment verified successfully",
  "status_code": 200,
  "easyslip_data": {
    "transRef": "A4fa65d187c154980",
    "amount": {
      "amount": 200
    },
    "receiver": {
      "account": {
        "name": {
          "th": "น.ส. พรปวีณ์ ส"
        }
      }
    }
  }
}
```

**Response (Validation Failed):**
```json
{
  "success": false,
  "message": "Validation failed",
  "errors": [
    "Amount is 150, must be 200",
    "Receiver name is 'นายสมชาย', must be 'น.ส. พรปวีณ์ ส'"
  ],
  "status_code": 400,
  "easyslip_data": {
    "transRef": "A4fa65d187c154980",
    "amount": {
      "amount": 150
    }
  }
}
```

### 5. Cronjob Management

#### `GET /cleanup/status`

ตรวจสอบสถานะ cronjob

**Response:**
```json
{
  "scheduler_running": true,
  "cron_enabled": true,
  "cleanup_minutes": 10,
  "jobs": [
    {
      "id": "cleanup_old_bookings",
      "name": "Cleanup Old Bookings",
      "next_run_time": "2024-01-15T10:35:00",
      "trigger": "cron[minute='*/5']"
    }
  ],
  "timestamp": "2024-01-15T10:30:00"
}
```

#### `POST /cleanup/old-bookings`

ลบ pending booking เก่าทันที

**Response:**
```json
{
  "success": true,
  "message": "Manual cleanup completed",
  "timestamp": "2024-01-15T10:30:00"
}
```

#### `POST /cleanup/start`

เริ่ม cronjob scheduler

**Response:**
```json
{
  "success": true,
  "message": "Cleanup scheduler started",
  "timestamp": "2024-01-15T10:30:00"
}
```

#### `POST /cleanup/stop`

หยุด cronjob scheduler

**Response:**
```json
{
  "success": true,
  "message": "Cleanup scheduler stopped",
  "timestamp": "2024-01-15T10:30:00"
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation failed"
}
```

### 404 Not Found
```json
{
  "detail": "Booking not found"
}
```

### 409 Conflict
```json
{
  "detail": "Booking already exists for this date. Please choose a different date."
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Environment Variables

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here

# EasySlip API Configuration
EASYSLIP_TOKEN=your_easyslip_access_token_here
EASYSLIP_URL=https://developer.easyslip.com/api/v1/verify
SLIP_BUCKET_NAME=payment-slips
TIME_DIFF_LIMIT=10
AMOUNT=200
RECEIVER_NAME=น.ส. พรปวีณ์ ส

# Cronjob Configuration
BOOKING_CLEANUP_MINUTES=10
CRON_ENABLED=true

# Server Configuration
PORT=8000
HOST=0.0.0.0
```

## Example Usage

### Get User's Bookings
```bash
curl -X GET "http://localhost:8000/bookings/user/user123"
```

### Get User's Pending Bookings
```bash
curl -X GET "http://localhost:8000/bookings/user/user123/pending"
```

### Create New Booking
```bash
curl -X POST "http://localhost:8000/create-booking" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "display_name": "John Doe",
    "selected_date": "2024-01-20",
    "amount": 200.0,
    "status": "pending"
  }'
```

### Update Booking
```bash
curl -X PUT "http://localhost:8000/bookings/booking_123" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "status=confirmed"
```

### Verify Slip
```bash
curl -X POST "http://localhost:8000/verify-slip-with-validation" \
  -F "payment_id=payment_123" \
  -F "user_id=user123" \
  -F "display_name=John Doe" \
  -F "selected_date=2024-01-20" \
  -F "amount=200" \
  -F "slip_image=@slip.jpg"
``` 