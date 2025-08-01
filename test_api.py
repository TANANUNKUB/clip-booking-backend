#!/usr/bin/env python3
"""
Test script for Clip Booking API
Run this script to test all endpoints
"""

import requests
import json
import time
from datetime import datetime, timedelta

# API base URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

def test_generate_payment():
    """Test payment generation"""
    print("\n💳 Testing payment generation...")
    try:
        data = {
            "userId": "test_user_123",
            "displayName": "Test User",
            "selectedDate": (datetime.now() + timedelta(days=1)).isoformat(),
            "amount": 1500.0
        }
        
        response = requests.post(f"{BASE_URL}/generate-payment", json=data)
        if response.status_code == 200:
            result = response.json()
            print("✅ Payment generation successful")
            print(f"   Payment ID: {result['paymentId']}")
            print(f"   QR Code URL: {result['qrCodeUrl']}")
            print(f"   Amount: {result['amount']}")
            return result['paymentId']
        else:
            print(f"❌ Payment generation failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Payment generation error: {e}")
        return None

def test_payment_status(payment_id):
    """Test payment status check"""
    print(f"\n📊 Testing payment status for {payment_id}...")
    try:
        response = requests.get(f"{BASE_URL}/payment-status/{payment_id}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Payment status check successful")
            print(f"   Status: {result['status']}")
            print(f"   Amount: {result['amount']}")
            return result['status']
        else:
            print(f"❌ Payment status check failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Payment status check error: {e}")
        return None

def test_confirm_booking(payment_id):
    """Test booking confirmation"""
    print(f"\n✅ Testing booking confirmation for {payment_id}...")
    try:
        data = {"paymentId": payment_id}
        response = requests.post(f"{BASE_URL}/confirm-booking", json=data)
        if response.status_code == 200:
            result = response.json()
            print("✅ Booking confirmation successful")
            print(f"   Booking ID: {result['bookingId']}")
            return result['bookingId']
        else:
            print(f"❌ Booking confirmation failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Booking confirmation error: {e}")
        return None

def test_get_bookings():
    """Test getting all bookings"""
    print("\n📋 Testing get bookings...")
    try:
        response = requests.get(f"{BASE_URL}/bookings")
        if response.status_code == 200:
            bookings = response.json()
            print(f"✅ Get bookings successful: {len(bookings)} bookings found")
            for booking in bookings:
                print(f"   - {booking['bookingId']}: {booking['displayName']} ({booking['status']})")
        else:
            print(f"❌ Get bookings failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Get bookings error: {e}")

def test_get_payments():
    """Test getting all payments"""
    print("\n💰 Testing get payments...")
    try:
        response = requests.get(f"{BASE_URL}/payments")
        if response.status_code == 200:
            payments = response.json()
            print(f"✅ Get payments successful: {len(payments)} payments found")
            for payment in payments:
                print(f"   - {payment['paymentId']}: {payment['displayName']} ({payment['status']})")
        else:
            print(f"❌ Get payments failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Get payments error: {e}")

def simulate_payment_completion(payment_id):
    """Simulate waiting for payment completion (2 minutes)"""
    print(f"\n⏳ Simulating payment completion for {payment_id}...")
    print("   Waiting 2 minutes for payment to be marked as successful...")
    
    # Wait for 2 minutes and check status every 30 seconds
    for i in range(4):
        time.sleep(30)
        status = test_payment_status(payment_id)
        if status == "success":
            print("✅ Payment completed successfully!")
            return True
    
    print("⚠️  Payment still pending after 2 minutes")
    return False

def main():
    """Run all tests"""
    print("🚀 Starting Clip Booking API Tests")
    print("=" * 50)
    
    # Test health check
    test_health_check()
    
    # Test payment generation
    payment_id = test_generate_payment()
    if not payment_id:
        print("❌ Cannot continue without payment ID")
        return
    
    # Test initial payment status
    test_payment_status(payment_id)
    
    # Test get payments
    test_get_payments()
    
    # Simulate payment completion
    payment_completed = simulate_payment_completion(payment_id)
    
    if payment_completed:
        # Test booking confirmation
        booking_id = test_confirm_booking(payment_id)
        if booking_id:
            # Test get bookings
            test_get_bookings()
    
    print("\n" + "=" * 50)
    print("🏁 Tests completed!")

if __name__ == "__main__":
    main() 