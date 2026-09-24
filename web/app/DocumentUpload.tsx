"use client";

import type { ChangeEvent, DragEvent } from "react";
import { useRef, useState } from "react";

import {
  uploadDocument,
  type UploadedDocument,
} from "@/lib/documents";

const MAX_FILE_BYTES = 1_000_000;

interface DocumentUploadProps {
  onUploaded: (document: UploadedDocument) => void;
}

export default function DocumentUpload({
  onUploaded,
}: DocumentUploadProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploaded, setUploaded] =
    useState<UploadedDocument | null>(null);
  const [uploadError, setUploadError] =
    useState<string | null>(null);

  async function handleFile(file: File): Promise<void> {
    setUploadError(null);
    setUploaded(null);

    if (!file.name.toLowerCase().endsWith(".txt")) {
      setUploadError("Only .txt files are supported.");
      return;
    }

    if (file.size > MAX_FILE_BYTES) {
      setUploadError("The file must not exceed 1 MB.");
      return;
    }

    setIsUploading(true);

    try {
      const document = await uploadDocument(file);
      setUploaded(document);
      onUploaded(document);
    } catch (error: unknown) {
      setUploadError(
        error instanceof Error
          ? error.message
          : "Document upload failed"
      );
    } finally {
      setIsUploading(false);
    }
  }

  function handleInputChange(
    event: ChangeEvent<HTMLInputElement>
  ): void {
    const file = event.target.files?.item(0);
    event.target.value = "";

    if (file) {
      void handleFile(file);
    }
  }

  function handleDrop(
    event: DragEvent<HTMLDivElement>
  ): void {
    event.preventDefault();
    setIsDragging(false);

    const file = event.dataTransfer.files.item(0);

    if (file) {
      void handleFile(file);
    }
  }

  return (
    <section className="mt-4 rounded-xl border border-slate-800 bg-slate-950 p-4">
      <h2 className="font-medium">Documents</h2>

      <div
        className={
          isDragging
            ? "mt-3 rounded-lg border-2 border-dashed border-blue-400 bg-blue-950 p-6 text-center"
            : "mt-3 rounded-lg border-2 border-dashed border-slate-700 p-6 text-center"
        }
        onDragEnter={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragOver={(event) => {
          event.preventDefault();
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
      >
        <input
          ref={inputRef}
          className="hidden"
          type="file"
          accept=".txt,text/plain"
          onChange={handleInputChange}
          disabled={isUploading}
        />

        <p className="text-sm text-slate-300">
          Drop a UTF-8 .txt file here
        </p>
        <p className="mt-1 text-xs text-slate-500">
          Maximum file size: 1 MB
        </p>

        <button
          className="mt-4 rounded-lg bg-slate-700 px-4 py-2 text-sm hover:bg-slate-600 disabled:opacity-50"
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={isUploading}
        >
          {isUploading ? "Uploading and indexing..." : "Choose file"}
        </button>
      </div>

      {uploadError ? (
        <p className="mt-3 rounded-lg bg-red-950 px-3 py-2 text-sm text-red-200">
          {uploadError}
        </p>
      ) : null}

      {uploaded ? (
        <div className="mt-3 rounded-lg bg-emerald-950 px-3 py-2 text-sm text-emerald-200">
          <p>{uploaded.filename} indexed successfully.</p>
          <p className="mt-1 text-xs">
            {uploaded.chunk_count} chunks ·{" "}
            {uploaded.embedding_dimensions} dimensions ·{" "}
            {uploaded.indexed_chunk_count} indexed
          </p>
        </div>
      ) : null}
    </section>
  );
}
