import { StreamChunk } from "../types/models";

export async function parseSseStream(
  response: Response,
  onChunk: (chunk: StreamChunk) => void
): Promise<void> {
  if (!response.body) {
    throw new Error("No response body available for streaming.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // SSE frames are separated by "\n\n"
      const chunks = buffer.split("\n\n");

      // Keep the last chunk in the buffer if it doesn't end with "\n\n"
      buffer = chunks.pop() || "";

      for (const chunk of chunks) {
        if (!chunk.trim()) continue;

        if (chunk.startsWith("data: ")) {
          const jsonStr = chunk.slice(6); // Remove "data: " prefix
          if (jsonStr === "[DONE]") {
            continue; // Standard SSE close, though our backend emits 'end' event
          }

          try {
            const data = JSON.parse(jsonStr) as StreamChunk;
            onChunk(data);
          } catch (e) {
            console.error("Failed to parse SSE JSON:", jsonStr, e);
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
