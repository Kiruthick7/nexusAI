# Nexus AI Operations Platform - Next.js Frontend

This directory contains the presentation-only frontend UI for the **Nexus AI Operations Platform**, developed as a high-fidelity visual demonstration of multi-agent expense orchestration.

---

## 🛠️ Stack

* **Next.js 15 (App Router)**
* **TypeScript**
* **Tailwind CSS**
* **shadcn/ui**
* **Framer Motion**
* **Lucide Icons**
* **Zustand (Global state registry)**

---

## 🚀 Running Locally

To run the Next.js development server:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) inside your web browser.

---

## 🏛️ Flow Boundary & State Control

This frontend is designed to consume Server-Sent Events (SSE) from the FastAPI backend:
1. All client-side state is centralized inside the **Zustand** store (`src/store/useStore.ts`).
2. Components strictly react to published state events, preventing inline business calculations.
3. The Stitch-generated layout serves as the absolute visual source of truth.
