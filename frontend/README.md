# RAG Frontend

This is the Next.js frontend for the Retrieval-Augmented Generation (RAG) platform. It provides a real-time conversational chat interface, a robust search debugging tool, and a system health dashboard.

## Local Development

To run this frontend locally, you must first ensure that the RAG backend is running and reachable.

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure environment:**
   Create a `.env.local` file in the root of the `frontend/` directory (or copy `.env.local.example`):
   ```env
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## Architecture & Routes

The application uses the Next.js App Router and is divided into three main sections:

- **`/` (Chat)**: The main conversational interface. Streams responses chunk-by-chunk using a custom Server-Sent Events (SSE) parser over a standard `POST /api/query` fetch request.
- **`/search` (Search Debug)**: A dedicated UI for testing retrieval strategies against `POST /api/search`. You can tune Top K, apply metadata filters, toggle cross-encoder reranking, and inspect raw debug metadata.
- **`/dashboard` (Health Observability)**: Polls the backend root paths (`/health`, `/ready`, `/live`) every 10 seconds to visualize the real-time status of the API, Redis cache, and Qdrant vector store.

---

## ⚠️ Important Troubleshooting: CORS

The single most common issue when connecting the frontend to the backend locally is a CORS (Cross-Origin Resource Sharing) rejection.

For local development to work, the backend's `.env` **must** include the frontend's origin in the `SECURITY_ALLOWED_ORIGINS` setting. 

If your frontend is running on `http://localhost:3000`, ensure your backend `.env` has:
```env
SECURITY_ALLOWED_ORIGINS='["http://localhost:3000"]'
```
*(Note: If you receive fetch errors or `ApiError` warnings in the browser console immediately upon sending a message, double-check this CORS setting on the backend.)*
