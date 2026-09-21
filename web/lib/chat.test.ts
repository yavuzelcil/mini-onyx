import {
  afterEach,
  describe,
  expect,
  jest,
  spyOn,
  test,
} from "bun:test";

import {
  createChatSession,
  getSessionMessages,
  sendChatMessage,
  streamChatMessage,
} from "@/lib/chat";
import type { StoredMessage } from "@/lib/chat";

afterEach(() => {
  jest.restoreAllMocks();
});

describe("sendChatMessage", () => {
  test("posts the message and returns the parsed reply", async () => {
    const fetchSpy = spyOn(globalThis, "fetch").mockResolvedValue(
      Response.json({
        reply: "Mini Onyx received: Hello",
      })
    );

    const response = await sendChatMessage("Hello");

    expect(fetchSpy).toHaveBeenCalledWith("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: "Hello",
      }),
    });

    expect(response).toEqual({
      reply: "Mini Onyx received: Hello",
    });
  });
});

describe("createChatSession", () => {
  test("creates a session with the selected persona", async () => {
    const session = {
      id: 7,
      title: "Ders",
      persona_name: "teacher",
    };
    const fetchSpy = spyOn(globalThis, "fetch").mockResolvedValue(
      Response.json(session, { status: 201 })
    );

    const result = await createChatSession("Ders", "teacher");

    expect(fetchSpy).toHaveBeenCalledWith("/api/chat/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: "Ders",
        persona_name: "teacher",
      }),
    });
    expect(result).toEqual(session);
  });
});

describe("getSessionMessages", () => {
  test("returns user and assistant messages for a session", async () => {
    const messages: StoredMessage[] = [
      { id: 1, role: "user", content: "Merhaba" },
      { id: 2, role: "assistant", content: "Selam" },
    ];
    const fetchSpy = spyOn(globalThis, "fetch").mockResolvedValue(
      Response.json(messages)
    );

    const result = await getSessionMessages(7);

    expect(fetchSpy).toHaveBeenCalledWith(
      "/api/chat/sessions/7/messages"
    );
    expect(result).toEqual(messages);
  });
});

describe("streamChatMessage", () => {
  test("reads NDJSON packets across network chunks", async () => {
    const encoder = new TextEncoder();
    const controller = new AbortController();

    const body = new ReadableStream<Uint8Array>({
      start(streamController) {
        streamController.enqueue(
          encoder.encode(
            '{"type":"content_delta","content":"Mer'
          )
        );
        streamController.enqueue(
          encoder.encode(
            'haba"}\n{"type":"done"}\n'
          )
        );
        streamController.close();
      },
    });

    const fetchSpy = spyOn(
      globalThis,
      "fetch"
    ).mockResolvedValue(
      new Response(body, {
        status: 200,
        headers: {
          "Content-Type": "application/x-ndjson",
        },
      })
    );

    const packets = [];

    for await (const packet of streamChatMessage(
      "Hello",
      controller.signal
    )) {
      packets.push(packet);
    }

    expect(fetchSpy).toHaveBeenCalledWith(
      "/api/chat/stream",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: "Hello",
        }),
        signal: controller.signal,
      }
    );

    expect(packets).toEqual([
      {
        type: "content_delta",
        content: "Merhaba",
      },
      {
        type: "done",
      },
    ]);
  });
});
