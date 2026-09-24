import {
  afterEach,
  describe,
  expect,
  jest,
  spyOn,
  test,
} from "bun:test";

import { uploadDocument } from "@/lib/documents";

afterEach(() => {
  jest.restoreAllMocks();
});

describe("uploadDocument", () => {
  test("uploads a text file as multipart form data", async () => {
    const uploaded = {
      id: 8,
      filename: "notes.txt",
      size_bytes: 12,
      character_count: 12,
      chunk_count: 1,
      embedding_dimensions: 1536,
      indexed_chunk_count: 1,
    };

    const fetchSpy = spyOn(globalThis, "fetch").mockResolvedValue(
      Response.json(uploaded, { status: 201 })
    );

    const file = new File(
      ["Mini Onyx"],
      "notes.txt",
      { type: "text/plain" }
    );

    const result = await uploadDocument(file);

    expect(result).toEqual(uploaded);

    const call = fetchSpy.mock.calls[0];

    if (!call) {
      throw new Error("Expected fetch to be called");
    }

    const [url, options] = call;

    expect(url).toBe("/api/documents/upload");
    expect(options?.method).toBe("POST");

    const body = options?.body;

    if (!(body instanceof FormData)) {
      throw new Error("Expected request body to be FormData");
    }

    expect(body.get("file")).toEqual(file);
  });

  test("uses the backend error detail", async () => {
    spyOn(globalThis, "fetch").mockResolvedValue(
      Response.json(
        { detail: "Only named .txt files are supported." },
        { status: 400 }
      )
    );

    const file = new File(
      ["content"],
      "notes.pdf",
      { type: "application/pdf" }
    );

    await expect(uploadDocument(file)).rejects.toThrow(
      "Only named .txt files are supported."
    );
  });
});
