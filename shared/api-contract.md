# Nexus AI Operations Platform - REST & SSE API Contracts

This document contains the official specifications of the REST endpoints and Server-Sent Events (SSE) interfaces exposed by the **Nexus AI Operations Platform** backend.

---

## 🚀 1. Endpoint Overview

### A. Create Claim Mission
* **Method**: `POST`
* **Path**: `/claims`
* **Content-Type**: `multipart/form-data`
* **Request Parameters**:
  - `file`: `UploadFile` (Optional receipt or invoice image/PDF)
* **Response Status**: `200 OK`
* **Response Body**:
  ```json
  {
    "mission_id": "RUN-9182",
    "claim_id": "CLM-4012"
  }
  ```
* **Description**: Initializes an evaluation mission, stores the state in memory, and schedules background processing. Immediately broadcasts a `workflow_started` event over SSE.

---

### B. Read Event Stream (SSE)
* **Method**: `GET`
* **Path**: `/claims/{mission_id}/events`
* **Headers**: `Accept: text/event-stream`
* **Query Parameters**:
  - `stream`: `boolean` (Default: `true`. Set to `false` in tests to retrieve catchup logs without entering infinite stream-waiting loops).
* **Response Status**: `200 OK`
* **Description**: Establishes a standard real-time Server-Sent Events link emitting progressive task execution details.

---

### C. System Diagnostics
* **Method**: `GET`
* **Path**: `/health`
* **Response Status**: `200 OK`
* **Response Body**:
  ```json
  {
    "status": "HEALTHY",
    "version": "1.0.0",
    "components": {
      "event_bus": "ACTIVE",
      "mission_manager": "ACTIVE"
    }
  }
  ```
