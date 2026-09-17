import {
  afterEach,
  describe,
  expect,
  jest,
  spyOn,
  test,
} from "bun:test";

import { sendChatMessage } from "@/lib/chat";

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
