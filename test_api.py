#!/usr/bin/env python3
"""
Pega-Python Integration Test Script
Bu script API endpoint'lerinizi test etmek için kullanılır
"""

import requests
import json
import time
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Health check testi"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_pega_webhook():
    """Pega webhook testi"""
    print("🔍 Testing Pega webhook...")
    
    # Departman değişikliği simülasyonu
    test_data = {
        "caseId": "HRSR-WORK-12345",
        "event": "department_change",
        "employeeId": "EMP001",
        "employeeName": "Ali Veli",
        "oldDepartment": "IT", 
        "newDepartment": "Finance",
        "effectiveDate": "2025-01-15",
        "hasFinancialAccess": True,
        "hasAdminRights": False,
        "accessToSensitiveData": True,
        "requestedBy": "HR Manager",
        "approvalRequired": True
    }
    
    response = requests.post(f"{BASE_URL}/webhook/pega", json=test_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        event_id = response.json().get("eventId")
        print(f"Event ID: {event_id}")
        
        # Biraz bekleyelim işlem tamamlansın
        print("⏳ Waiting for processing...")
        time.sleep(2)
        
        # Event detaylarını kontrol edelim
        print("🔍 Checking event details...")
        detail_response = requests.get(f"{BASE_URL}/events/{event_id}")
        if detail_response.status_code == 200:
            event_detail = detail_response.json()
            print(f"Event Status: {event_detail['status']}")
            if event_detail.get('processing_result'):
                print(f"Processing Result: {json.dumps(event_detail['processing_result'], indent=2)}")
    print()

def test_onboarding_event():
    """Yeni çalışan onboarding testi"""
    print("🔍 Testing employee onboarding...")
    
    test_data = {
        "caseId": "HRSR-WORK-12346",
        "event": "employee_onboarding",
        "employeeId": "EMP002",
        "employeeName": "Fatma Öz",
        "department": "Marketing",
        "position": "Digital Marketing Specialist",
        "startDate": "2025-01-20",
        "manager": "Marketing Director",
        "needsLaptop": True,
        "needsBadge": True,
        "systemAccess": ["CRM", "Marketing Tools", "Email"]
    }
    
    response = requests.post(f"{BASE_URL}/webhook/pega", json=test_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_offboarding_event():
    """Çalışan çıkış testi"""
    print("🔍 Testing employee offboarding...")
    
    test_data = {
        "caseId": "HRSR-WORK-12347", 
        "event": "employee_offboarding",
        "employeeId": "EMP003",
        "employeeName": "Mehmet Kaya",
        "department": "Sales",
        "lastWorkingDay": "2025-01-31",
        "reason": "Resignation",
        "hasCompanyAssets": True,
        "needsKnowledgeTransfer": True
    }
    
    response = requests.post(f"{BASE_URL}/webhook/pega", json=test_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_list_events():
    """Event listesi testi"""
    print("🔍 Testing events list...")
    
    response = requests.get(f"{BASE_URL}/events?limit=5")
    print(f"Status: {response.status_code}")
    events = response.json()
    print(f"Found {len(events)} events")
    
    for event in events:
        print(f"- Event {event['id']}: {event['event']} (Case: {event['caseId']}) - Status: {event['status']}")
    print()

def test_metrics():
    """Metrik testi"""
    print("🔍 Testing metrics...")
    
    response = requests.get(f"{BASE_URL}/metrics")
    print(f"Status: {response.status_code}")
    metrics = response.json()
    print(f"Total events (7 days): {metrics['total']}")
    print(f"Event breakdown: {metrics['by_event']}")
    print()

def test_dashboard():
    """Dashboard testi"""
    print("🔍 Testing dashboard...")
    
    response = requests.get(f"{BASE_URL}/dashboard")
    print(f"Status: {response.status_code}")
    dashboard = response.json()
    print(f"Total events (24h): {dashboard['total_events']}")
    print(f"Pega connection: {dashboard['pega_connection']}")
    print(f"Status breakdown: {dashboard['status_breakdown']}")
    print()

def main():
    """Ana test fonksiyonu"""
    print("🚀 Starting Pega-Python Integration Tests")
    print("=" * 50)
    
    try:
        test_health()
        test_pega_webhook()
        test_onboarding_event() 
        test_offboarding_event()
        test_list_events()
        test_metrics()
        test_dashboard()
        
        print("✅ All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    main()
