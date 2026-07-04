# Deployment Guide

This guide will walk you through deploying your RAG Application to the cloud using **Vercel** for the frontend and a service like **Render** or **Railway** for the backend.

## Prerequisites
1. **GitHub Account**: Your code is already pushed to GitHub.
2. Accounts on the platforms you choose (Vercel, Render/Railway, Supabase/Qdrant/Upstash).

---

## 1. Set Up Managed Databases
Your application uses PostgreSQL (Supabase), Qdrant (Vector DB), and Redis. Since you are deploying to serverless/PaaS platforms, you need hosted versions of these databases.

*   **PostgreSQL**: Your `.env` already points to `aws-1-ap-southeast-2.pooler.supabase.com`. Ensure that database is accessible from the internet.
*   **Qdrant**: Create a free cluster on [Qdrant Cloud](https://cloud.qdrant.io/). Get the **Cluster URL** and an **API Key**.
*   **Redis**: Create a free Redis instance on [Upstash](https://upstash.com/) or [Render](https://render.com/). Get the **Redis URL** (e.g., `rediss://default:password@region.upstash.io:6379`).

---

## 2. Deploy the Backend (Render or Railway)
Your backend is fully Dockerized (`backend/Dockerfile`), which makes deploying it to a container platform very easy.

### Option A: Using Render (Recommended for Free Tier)
1. Go to [Render](https://render.com/) and create a new **Web Service**.
2. Connect your GitHub account and select the `RAG_application` repository.
3. **Settings**:
    *   **Name**: `rag-backend`
    *   **Root Directory**: `backend` (This is crucial so Render finds your `Dockerfile` and `pyproject.toml`).
    *   **Environment**: Select `Docker`.
4. **Environment Variables**: Add all the variables from your `backend/.env` file. Be sure to include your new Qdrant and Redis URLs:
    *   `QDRANT_URL`: `https://your-cluster.aws.cloud.qdrant.io:6333`
    *   `QDRANT_API_KEY`: `your-qdrant-api-key`
    *   `REDIS_URL`: `rediss://...`
    *   *Also include your Supabase DB variables, Groq API key, etc.*
5. Click **Create Web Service**. Render will build the Docker image and deploy it.
6. Once deployed, copy the **Render URL** (e.g., `https://rag-backend-xxx.onrender.com`).

---

## 3. Deploy the Frontend (Vercel)
1. Go to [Vercel](https://vercel.com/) and click **Add New Project**.
2. Import the `RAG_application` repository from your GitHub.
3. **Settings**:
    *   **Project Name**: `rag-frontend`
    *   **Framework Preset**: Next.js
    *   **Root Directory**: Click "Edit" and select `frontend`.
4. **Environment Variables**:
    *   Add `NEXT_PUBLIC_API_BASE_URL` and set its value to your **Render Backend URL** (e.g., `https://rag-backend-xxx.onrender.com`).
    *   Add `NEXT_PUBLIC_MAX_CONTEXT_TOKENS` (e.g., `16384`).
5. Click **Deploy**.

---

## 4. Final Steps
*   Once Vercel finishes deploying, visit the provided Vercel URL.
*   Your frontend will now securely communicate with your live backend!
*   **Important**: In your backend environment variables on Render, remember to update `FRONTEND_BASE_URL` and `SECURITY_ALLOWED_ORIGINS` to include your new Vercel domain so CORS isn't blocked. (e.g., `SECURITY_ALLOWED_ORIGINS='["https://your-frontend.vercel.app"]'`).
