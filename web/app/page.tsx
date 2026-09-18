"use client";

import type { FormEvent } from "react";
import { useRef, useState } from "react";

import { streamChatMessage } from "@/lib/chat";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export default function HomePage() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ): Promise<void> {
    event.preventDefault();

    const normalizedMessage = message.trim();

    if (!normalizedMessage || isSubmitting) {
      return;
    }

    const userMessageId = crypto.randomUUID();
    const assistantMessageId = crypto.randomUUID();
    const abortController = new AbortController();

    abortControllerRef.current = abortController;

    setError(null);
    setIsSubmitting(true);
    setMessage("");

    setMessages((currentMessages) => [
      ...currentMessages,
      {
        id: userMessageId,
        role: "user",
        content: normalizedMessage,
      },
      {
        id: assistantMessageId,
        role: "assistant",
        content: "",
      },
    ]);

    let receivedDone = false;

    try {
      for await (const packet of streamChatMessage(
        normalizedMessage,
        abortController.signal
      )) {
        if (packet.type === "content_delta") {
          setMessages((currentMessages) =>
            currentMessages.map((chatMessage) =>
              chatMessage.id === assistantMessageId
                ? {
                    ...chatMessage,
                    content:
                      chatMessage.content + packet.content,
                  }
                : chatMessage
            )
          );
        }

        if (packet.type === "error") {
          throw new Error(packet.detail);
        }

        if (packet.type === "done") {
          receivedDone = true;
        }
      }

      if (!receivedDone) {
        throw new Error("Chat stream ended unexpectedly");
      }
    } catch (requestError: unknown) {
      if (
        requestError instanceof DOMException &&
        requestError.name === "AbortError"
      ) {
        return;
      }

      const detail =
        requestError instanceof Error
          ? requestError.message
          : "An unexpected error occurred";

      setError(detail);
    } finally {
      if (abortControllerRef.current === abortController) {
        abortControllerRef.current = null;
      }

      setIsSubmitting(false);
    }
  }

  function handleStop(): void {
    abortControllerRef.current?.abort();
  }

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-12 text-slate-100">
      <section className="mx-auto flex min-h-[80vh] max-w-3xl flex-col rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
        <header className="border-b border-slate-800 pb-4">
          <h1 className="text-2xl font-semibold">Mini Onyx</h1>
          <p className="mt-1 text-sm text-slate-400">
            First end-to-end chat flow
          </p>
        </header>

        <div
          className="flex flex-1 flex-col gap-4 py-6"
          aria-live="polite"
        >
          {messages.length === 0 ? (
            <p className="text-center text-slate-500">
              Send a message to start.
            </p>
          ) : (
            messages.map((chatMessage) => (
              <article
                key={chatMessage.id}
                className={
                  chatMessage.role === "user"
                    ? "ml-auto max-w-[80%] rounded-xl bg-blue-600 px-4 py-3"
                    : "mr-auto max-w-[80%] rounded-xl bg-slate-800 px-4 py-3"
                }
              >
                <p className="text-xs font-semibold uppercase opacity-70">
                  {chatMessage.role}
                </p>
                <p className="mt-1 whitespace-pre-wrap">
                  {chatMessage.content}
                </p>
              </article>
            ))
          )}

          {error ? (
            <p className="rounded-lg bg-red-950 px-4 py-3 text-red-200">
              {error}
            </p>
          ) : null}
        </div>

        <form
          className="flex gap-3 border-t border-slate-800 pt-4"
          onSubmit={handleSubmit}
        >
          <label className="sr-only" htmlFor="message">
            Message
          </label>

          <input
            id="message"
            className="min-w-0 flex-1 rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-blue-500"
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Write a message..."
            disabled={isSubmitting}
          />

          {isSubmitting ? (
            <button
              className="rounded-lg bg-red-600 px-5 py-3 font-medium hover:bg-red-500"
              type="button"
              onClick={handleStop}
            >
              Stop
            </button>
          ) : (
            <button
              className="rounded-lg bg-blue-600 px-5 py-3 font-medium hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
              type="submit"
              disabled={!message.trim()}
            >
              Send
            </button>
          )}
        </form>
      </section>
    </main>
  );
}
