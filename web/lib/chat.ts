const CHAT_ENDPOINT = "/api/chat";
const CHAT_STREAM_ENDPOINT = "/api/chat/stream";

export interface ChatRequest {
  message: string;
}

export interface ChatResponse {
  reply: string;
}

export interface ChatStreamDelta {
  type: "content_delta";
  content: string;
}

export interface ChatStreamDone {
  type: "done";
}

export interface ChatStreamError {
  type: "error";
  detail: string;
}

export type ChatStreamPacket =
  | ChatStreamDelta
  | ChatStreamDone
  | ChatStreamError;

function isChatResponse(value: unknown): value is ChatResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "reply" in value &&
    typeof value.reply === "string"
  );
}

function isChatStreamPacket(
  value: unknown
): value is ChatStreamPacket {
  if (
    typeof value !== "object" ||
    value === null ||
    !("type" in value)
  ) {
    return false;
  }

  if (value.type === "content_delta") {
    return (
      "content" in value &&
      typeof value.content === "string"
    );
  }

  if (value.type === "done") {
    return true;
  }

  if (value.type === "error") {
    return (
      "detail" in value &&
      typeof value.detail === "string"
    );
  }

  return false;
}

function parseChatStreamPacket(line: string): ChatStreamPacket {
  const payload: unknown = JSON.parse(line);

  if (!isChatStreamPacket(payload)) {
    throw new Error("Backend returned an invalid stream packet");
  }

  return payload;
}

export async function sendChatMessage(
  message: string
): Promise<ChatResponse> {
  const request: ChatRequest = {
    message,
  };

  const response = await fetch(CHAT_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Chat request failed with status ${response.status}`);
  }

  const payload: unknown = await response.json();

  if (!isChatResponse(payload)) {
    throw new Error("Backend returned an invalid chat response");
  }

  return payload;
}

export async function* streamChatMessage(
  message: string,
  signal?: AbortSignal
): AsyncGenerator<ChatStreamPacket, void, unknown> {
  const request: ChatRequest = {
    message,
  };

  const response = await fetch(CHAT_STREAM_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
    signal,
  });

  if (!response.ok) {
    throw new Error(
      `Chat stream failed with status ${response.status}`
    );
  }

  if (!response.body) {
    throw new Error("Backend returned an empty stream");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { value, done } = await reader.read();

      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        const normalizedLine = line.trim();

        if (normalizedLine) {
          yield parseChatStreamPacket(normalizedLine);
        }
      }
    }

    buffer += decoder.decode();

    const finalLine = buffer.trim();

    if (finalLine) {
      yield parseChatStreamPacket(finalLine);
    }
  } finally {
    reader.releaseLock();
  }
}
