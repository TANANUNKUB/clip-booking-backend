# Clip Booking API

A FastAPI-based backend service for managing clip editing bookings with payment integration and Supabase database.

## Features

- 🚀 FastAPI with automatic API documentation
- 💳 Payment generation with QR codes
- 📅 Booking management system
- 🗄️ Supabase database integration
- 🐳 Docker support for production deployment
- 🔒 CORS middleware for frontend integration
- 📊 Health check endpoints

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Supabase account and project

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd clip-booking-backend
```

### 2. Environment Configuration

Copy the example environment file and configure your Supabase credentials:

```bash
cp env.example .env
```

Edit `.env` with your Supabase project details:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
```

### 3. Supabase Database Setup

Create the following tables in your Supabase project:

#### Payments Table
```sql
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    payment_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    selected_date TIMESTAMP NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    qr_code_url TEXT,
    paid_at TIMESTAMP
);
```

#### Bookings Table
```sql
CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    booking_id VARCHAR(255) UNIQUE NOT NULL,
    payment_id VARCHAR(255) REFERENCES payments(payment_id),
    user_id VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    selected_date TIMESTAMP NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'confirmed',
    confirmed_at TIMESTAMP DEFAULT NOW()
);
```

### 4. Run with Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 5. Run Locally (Alternative)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

### Endpoints

#### POST /generate-payment
Generate a new payment and QR code.

**Request Body:**
```json
{
    "userId": "user_123",
    "displayName": "John Doe",
    "selectedDate": "2024-01-15T10:00:00",
    "amount": 1500.0
}
```

**Response:**
```json
{
    "paymentId": "payment_1703123456_abc123def",
    "qrCodeUrl": "https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=payment_1703123456_abc123def",
    "amount": 1500.0
}
```

#### GET /payment-status/{payment_id}
Check payment status (simulates payment completion after 2 minutes).

**Response:**
```json
{
    "paymentId": "payment_1703123456_abc123def",
    "status": "pending",
    "amount": 1500.0,
    "paidAt": null
}
```

#### POST /confirm-booking
Confirm booking after successful payment.

**Request Body:**
```json
{
    "paymentId": "payment_1703123456_abc123def"
}
```

**Response:**
```json
{
    "success": true,
    "bookingId": "booking_1703123456_xyz789ghi"
}
```

#### GET /bookings
Get all bookings (debug endpoint).

#### GET /payments
Get all payments (debug endpoint).

#### GET /health
Health check endpoint.

## Testing

### Using curl

```bash
# Generate payment
curl -X POST "http://localhost:8000/generate-payment" \
     -H "Content-Type: application/json" \
     -d '{
       "userId": "user_123",
       "displayName": "John Doe",
       "selectedDate": "2024-01-15T10:00:00",
       "amount": 1500.0
     }'

# Check payment status
curl "http://localhost:8000/payment-status/payment_1703123456_abc123def"

# Confirm booking
curl -X POST "http://localhost:8000/confirm-booking" \
     -H "Content-Type: application/json" \
     -d '{"paymentId": "payment_1703123456_abc123def"}'
```

### Using the API Documentation

1. Open `http://localhost:8000/docs` in your browser
2. Click on any endpoint to expand it
3. Click "Try it out" to test the endpoint
4. Fill in the required parameters and click "Execute"

## Production Deployment

### Docker Production Build

```bash
# Build production image
docker build -t clip-booking-api:latest .

# Run with environment variables
docker run -d \
  -p 8000:8000 \
  -e SUPABASE_URL=your_supabase_url \
  -e SUPABASE_ANON_KEY=your_supabase_key \
  clip-booking-api:latest
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Your Supabase project URL | Yes |
| `SUPABASE_ANON_KEY` | Your Supabase anonymous key | Yes |

## Development

### Project Structure

```
clip-booking-backend/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose configuration
├── env.example         # Environment variables template
└── README.md           # This file
```

### Adding New Features

1. Add new Pydantic models in `main.py`
2. Create new endpoints with proper error handling
3. Update the database schema if needed
4. Add tests for new functionality
5. Update this README with new endpoint documentation

## Troubleshooting

### Common Issues

1. **Supabase Connection Error**: Verify your `SUPABASE_URL` and `SUPABASE_ANON_KEY` are correct
2. **Database Table Not Found**: Ensure you've created the required tables in Supabase
3. **Port Already in Use**: Change the port in `docker-compose.yml` or stop other services using port 8000

### Logs

```bash
# View Docker logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f clip-booking-api
```

## License

This project is licensed under the MIT License. 