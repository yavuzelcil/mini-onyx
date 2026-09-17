const CHAT_ENDPOINT = "/api/chat";

export interface ChatRequest {
  message: string;
}

export interface ChatResponse {
  reply: string;
}

function isChatResponse(value: unknown): value is ChatResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "reply" in value &&
    typeof value.reply === "string"
  );
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
