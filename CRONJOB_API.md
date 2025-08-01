# Cronjob API Documentation

## Overview

ระบบ Cronjob สำหรับลบ **pending bookings** ที่เก่ากว่า 10 นาที (หรือตามที่กำหนดใน `BOOKING_CLEANUP_MINUTES`) โดยทำงานทุก 5 นาที

## Configuration

### Environment Variables

```env
# Cronjob Configuration
BOOKING_CLEANUP_MINUTES=10    # จำนวนนาทีที่ pending booking จะถูกลบ (default: 10)
CRON_ENABLED=true             # เปิด/ปิด cronjob (true/false)
```

## API Endpoints

### 1. Manual Cleanup

#### `POST /cleanup/old-bookings`

เรียกใช้การลบ pending booking เก่าทันที (ไม่ต้องรอ cronjob)

**Response:**
```json
{
  "success": true,
  "message": "Manual cleanup completed",
  "timestamp": "2024-01-15T10:30:00"
}
```

### 2. Check Cronjob Status

#### `GET /cleanup/status`

ตรวจสอบสถานะของ cronjob scheduler

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

### 3. Start Scheduler

#### `POST /cleanup/start`

เริ่มต้น cronjob scheduler

**Response:**
```json
{
  "success": true,
  "message": "Cleanup scheduler started",
  "timestamp": "2024-01-15T10:30:00"
}
```

### 4. Stop Scheduler

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

## How It Works

### Automatic Cleanup
- Cronjob จะทำงานทุก 5 นาที
- ตรวจสอบ booking ที่มี `status = "pending"` และ `created_at` เก่ากว่า `BOOKING_CLEANUP_MINUTES` นาที
- ลบเฉพาะ pending booking ที่เก่าออกโดยอัตโนมัติ
- บันทึก log การทำงาน

### Manual Cleanup
- สามารถเรียกใช้ API `/cleanup/old-bookings` เพื่อลบทันที
- ไม่ต้องรอ cronjob

### Booking Status Filter
- **ลบเฉพาะ**: `status = "pending"`
- **ไม่ลบ**: `status = "confirmed"`, `status = "cancelled"`, หรือ status อื่นๆ

## Logging

ระบบจะบันทึก log ดังนี้:
- `INFO`: เริ่มต้น cleanup, ไม่พบ pending booking เก่า, cleanup เสร็จสิ้น
- `ERROR`: เกิดข้อผิดพลาดในการลบ booking หรือ scheduler

## Example Usage

### 1. ตรวจสอบสถานะ
```bash
curl -X GET "http://localhost:8000/cleanup/status"
```

### 2. ลบ pending booking เก่าทันที
```bash
curl -X POST "http://localhost:8000/cleanup/old-bookings"
```

### 3. หยุด cronjob
```bash
curl -X POST "http://localhost:8000/cleanup/stop"
```

### 4. เริ่ม cronjob
```bash
curl -X POST "http://localhost:8000/cleanup/start"
```

## Configuration Examples

### ลบ pending booking เก่ากว่า 5 นาที
```env
BOOKING_CLEANUP_MINUTES=5
```

### ปิด cronjob
```env
CRON_ENABLED=false
```

### เปิด cronjob
```env
CRON_ENABLED=true
```

## Notes

- Cronjob จะเริ่มทำงานอัตโนมัติเมื่อ server เริ่มต้น
- สามารถปิด/เปิด cronjob ได้ผ่าน API หรือ environment variable
- **ลบเฉพาะ pending bookings เท่านั้น** - booking ที่ confirmed แล้วจะไม่ถูกลบ
- การลบ booking จะไม่ส่งผลกระทบต่อ payment records
- ระบบจะบันทึก log ทุกการทำงานเพื่อการตรวจสอบ
- ทำงานทุก 5 นาที (ไม่ใช่ทุกนาทีแล้ว) 