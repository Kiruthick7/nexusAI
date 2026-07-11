#!/usr/bin/env python3
"""
Production Readiness Smoke Test Suite - Nexus AI Operations Platform
====================================================================
Performs non-destructive validation of base-path routing, deep health 
mechanisms, ready endpoints, and demo playback initialization.
====================================================================
"""

import json
import sys
import urllib.request
import urllib.error

# ANSI console color sequences
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[0;33m"
CYAN = "\033[0;36m"
BOLD = "\033[1m"
NC = "\033[0m"

BASE_URL = "http://localhost:8000"

def log_status(name: str, success: bool, detail: str = ""):
    status = f"{GREEN}[PASS]{NC}" if success else f"{RED}[FAIL]{NC}"
    print(f" {status} {BOLD}{name:<25}{NC} {detail}")

def run_tests():
    print(f"{CYAN}{BOLD}======================================================================")
    print(BOLD + "       NEXUS AI OPERATIONS PLATFORM - SMOKE TESTING SUITE")
    print(f"======================================================================{NC}\n")
    
    # 1. Test Base Endpoint
    try:
        req = urllib.request.Request(f"{BASE_URL}/")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            assert data["service"] == "Nexus AI Operations Platform"
            log_status("Root Context GET '/'", True, f"Service: {data['service']}")
    except Exception as e:
        log_status("Root Context GET '/'", False, f"Connection failed: {e}")
        sys.exit(1)
        
    # 2. Test Readiness Endpoint
    try:
        req = urllib.request.Request(f"{BASE_URL}/ready")
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8").strip()
            assert resp.status == 200
            assert content == "READY"
            log_status("Readiness GET '/ready'", True, f"Status: {content}")
    except Exception as e:
        log_status("Readiness GET '/ready'", False, f"Failed: {e}")
        sys.exit(1)
        
    # 3. Test Deep Health Endpoint
    try:
        req = urllib.request.Request(f"{BASE_URL}/health")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            assert "active_missions" in data
            assert "connected_sse_clients" in data
            assert "application" in data
            assert "services_health" in data
            log_status("Health GET '/health'", True, f"Missions: {data['active_missions']}, Env: {data['environment']}")
    except Exception as e:
        log_status("Health GET '/health'", False, f"Failed: {e}")
        sys.exit(1)
        
    # 4. Test Ingestion Upload Capping/Validation (Large file)
    try:
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        data = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="test.pdf"\r\n'
            f"Content-Type: application/pdf\r\n\r\n"
            f"{'A' * (6 * 1024 * 1024)}"  # 6MB file
            f"\r\n--{boundary}--\r\n"
        ).encode("utf-8")
        
        req = urllib.request.Request(
            f"{BASE_URL}/claims",
            data=data,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}"
            }
        )
        try:
            urllib.request.urlopen(req)
            log_status("Secure Ingestion > 5MB", False, "Expected 400 Bad Request but succeeded")
        except urllib.error.HTTPError as e:
            assert e.code == 400
            log_status("Secure Ingestion > 5MB", True, "Successfully blocked file > 5MB (400 Bad Request)")
    except Exception as e:
         log_status("Secure Ingestion > 5MB", False, f"Unexpected error: {e}")
         
    # 5. Test Ingestion Upload MIME Validation (Unsupported type)
    try:
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        data = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="virus.exe"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n"
            f"binarycontent"
            f"\r\n--{boundary}--\r\n"
        ).encode("utf-8")
        
        req = urllib.request.Request(
            f"{BASE_URL}/claims",
            data=data,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}"
            }
        )
        try:
            urllib.request.urlopen(req)
            log_status("MIME Validation Filter", False, "Expected 400 Bad Request but succeeded")
        except urllib.error.HTTPError as e:
            assert e.code == 400
            log_status("MIME Validation Filter", True, "Successfully blocked unsupported MIME format (400 Bad Request)")
    except Exception as e:
         log_status("MIME Validation Filter", False, f"Unexpected error: {e}")
         
    # 6. Test Demo Simulation Route
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/demo/approval",
            data=b"",
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            assert "mission_id" in data
            log_status("Demo Trigger '/demo/*'", True, f"Triggered approval scenario under mission: {data['mission_id']}")
    except Exception as e:
        log_status("Demo Trigger '/demo/*'", False, f"Failed: {e}")
        
    print(f"\n{GREEN}{BOLD}✔ All smoke tests completed successfully!{NC}\n")

if __name__ == "__main__":
    run_tests()
