export interface Persona {
  name: string;
}

export interface ChatSession {
  id: number;
  title: string;
  persona_name: string | null;
}

export interface StoredMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
}

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

async function* streamChatAtEndpoint(
  endpoint: string,
  message: string,
  signal?: AbortSignal
): AsyncGenerator<ChatStreamPacket, void, unknown> {
  const request: ChatRequest = {
    message,
  };

  const response = await fetch(endpoint, {
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

export async function* streamChatMessage(
  message: string,
  signal?: AbortSignal
): AsyncGenerator<ChatStreamPacket, void, unknown> {
  yield* streamChatAtEndpoint(CHAT_STREAM_ENDPOINT, message, signal);
}

export async function* streamSessionMessage(
  sessionId: number,
  message: string,
  signal?: AbortSignal
): AsyncGenerator<ChatStreamPacket, void, unknown> {
  yield* streamChatAtEndpoint(
    `/api/chat/sessions/${sessionId}/messages/stream`,
    message,
    signal
  );
}


function isChatSession(value: unknown): value is ChatSession {
  return (
    typeof value === "object" &&
    value !== null &&
    "id" in value &&
    typeof value.id === "number" &&
    "title" in value &&
    typeof value.title === "string" &&
    "persona_name" in value &&
    (value.persona_name === null ||
      typeof value.persona_name === "string")
  );
}

function isPersona(value: unknown): value is Persona {
  return (
    typeof value === "object" &&
    value !== null &&
    "name" in value &&
    typeof value.name === "string"
  );
}

function isStoredMessage(value: unknown): value is StoredMessage {
  return (
    typeof value === "object" &&
    value !== null &&
    "id" in value &&
    typeof value.id === "number" &&
    "role" in value &&
    (value.role === "user" || value.role === "assistant") &&
    "content" in value &&
    typeof value.content === "string"
  );
}

export async function createChatSession(
  title: string,
  personaName: string | null = null
): Promise<ChatSession> {
  const response = await fetch("/api/chat/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title,
      persona_name: personaName,
    }),
  });

  if (!response.ok) {
    throw new Error(`Session creation failed with status ${response.status}`);
  }

  const payload: unknown = await response.json();

  if (!isChatSession(payload)) {
    throw new Error("Backend returned an invalid chat session");
  }

  return payload;
}

export async function getChatSession(sessionId: number): Promise<ChatSession> {
  const response = await fetch(`/api/chat/sessions/${sessionId}`);

  if (!response.ok) {
    throw new Error(`Session lookup failed with status ${response.status}`);
  }

  const payload: unknown = await response.json();

  if (!isChatSession(payload)) {
    throw new Error("Backend returned an invalid chat session");
  }

  return payload;
}

export async function fetchPersonas(): Promise<Persona[]> {
  const response = await fetch("/api/chat/personas");

  if (!response.ok) {
    throw new Error(`Persona list failed with status ${response.status}`);
  }

  const payload: unknown = await response.json();

  if (!Array.isArray(payload) || !payload.every(isPersona)) {
    throw new Error("Backend returned invalid personas");
  }

  return payload;
}

export async function getSessionMessages(
  sessionId: number
): Promise<StoredMessage[]> {
  const response = await fetch(`/api/chat/sessions/${sessionId}/messages`);

  if (!response.ok) {
    throw new Error(`Message history failed with status ${response.status}`);
  }

  const payload: unknown = await response.json();

  if (!Array.isArray(payload) || !payload.every(isStoredMessage)) {
    throw new Error("Backend returned invalid message history");
  }

  return payload;
}
