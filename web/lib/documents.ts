export interface UploadedDocument {
  id: number;
  filename: string;
  size_bytes: number;
  character_count: number;
  chunk_count: number;
  embedding_dimensions: number;
  indexed_chunk_count: number;
}

function isUploadedDocument(
  value: unknown
): value is UploadedDocument {
  return (
    typeof value === "object" &&
    value !== null &&
    "id" in value &&
    typeof value.id === "number" &&
    "filename" in value &&
    typeof value.filename === "string" &&
    "size_bytes" in value &&
    typeof value.size_bytes === "number" &&
    "character_count" in value &&
    typeof value.character_count === "number" &&
    "chunk_count" in value &&
    typeof value.chunk_count === "number" &&
    "embedding_dimensions" in value &&
    typeof value.embedding_dimensions === "number" &&
    "indexed_chunk_count" in value &&
    typeof value.indexed_chunk_count === "number"
  );
}

export async function uploadDocument(
  file: File
): Promise<UploadedDocument> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("/api/documents/upload", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let detail = `Document upload failed with status ${response.status}`;

    try {
      const payload: unknown = await response.json();

      if (
        typeof payload === "object" &&
        payload !== null &&
        "detail" in payload &&
        typeof payload.detail === "string"
      ) {
        detail = payload.detail;
      }
    } catch {
      // Response did not contain JSON error details.
    }

    throw new Error(detail);
  }

  const payload: unknown = await response.json();

  if (!isUploadedDocument(payload)) {
    throw new Error("Backend returned an invalid document response");
  }

  return payload;
}
