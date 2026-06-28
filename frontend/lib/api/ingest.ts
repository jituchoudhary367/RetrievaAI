import { apiBaseUrl } from "./client";

export interface FileIngestResult {
  path: string;
  status: string;
  num_chunks: number;
  error?: string;
  warnings: string[];
}

export interface IngestionReport {
  total_files: number;
  indexed: number;
  skipped: number;
  failed: number;
  results: FileIngestResult[];
  elapsed_seconds: number;
}

export async function uploadAndIngest(file: File): Promise<IngestionReport> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${apiBaseUrl}/api/v1/ingest/upload`, {
    method: "POST",
    // Do not set Content-Type header. Let the browser set it to multipart/form-data with the boundary.
    body: formData,
  });

  if (!response.ok) {
    let errorMessage = "Failed to upload file";
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorMessage = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
      }
    } catch (e) {
      // Ignore JSON parse error if response is not JSON
    }
    throw new Error(errorMessage);
  }

  return response.json();
}
