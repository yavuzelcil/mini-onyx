"use client";

import type { FormEvent } from "react";
import { useEffect, useRef, useState } from "react";

import {
  createChatSession,
  getChatSession,
  getSessionMessages,
  streamSessionMessage,
  type ChatSource,
} from "@/lib/chat";
import PersonaSelect from "@/app/PersonaSelect";
import DocumentUpload from "@/app/DocumentUpload";

const SESSION_STORAGE_KEY = "mini-onyx-session-id";


interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources: ChatSource[];
}

export default function HomePage() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [selectedPersona, setSelectedPersona] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const abortControllerRef = useRef<AbortController | null>(null);
  const [useRag, setUseRag] = useState(false);

  useEffect(() => {
    const savedId = window.localStorage.getItem(SESSION_STORAGE_KEY);
    const parsedId = Number(savedId);

    if (!savedId || !Number.isInteger(parsedId) || parsedId < 1) {
      window.localStorage.removeItem(SESSION_STORAGE_KEY);
      setIsLoadingHistory(false);
      return;
    }

    let cancelled = false;

    async function restoreSession(): Promise<void> {
      try {
        const [session, storedMessages] = await Promise.all([
          getChatSession(parsedId),
          getSessionMessages(parsedId),
        ]);

        if (cancelled) {
          return;
        }

        setSessionId(session.id);
        setSelectedPersona(session.persona_name);
        setMessages(
          storedMessages.map((stored) => ({
            id: String(stored.id),
            role: stored.role,
            content: stored.content,
            sources: [],
          }))
        );
      } catch (restoreError: unknown) {
        if (!cancelled) {
          setError(
            restoreError instanceof Error
              ? restoreError.message
              : "Could not restore chat history"
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoadingHistory(false);
        }
      }
    }

    void restoreSession();
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ): Promise<void> {
    event.preventDefault();

    const normalizedMessage = message.trim();

    if (!normalizedMessage || isSubmitting || isLoadingHistory) {
      return;
    }

    const userMessageId = crypto.randomUUID();
    const assistantMessageId = crypto.randomUUID();
    const abortController = new AbortController();

    abortControllerRef.current = abortController;

    setError(null);
    setIsSubmitting(true);
    setMessage("");

    let receivedDone = false;
    let messagesAdded = false;

    try {
      let activeSessionId = sessionId;
      if (activeSessionId === null) {
        const session = await createChatSession(
          normalizedMessage.slice(0, 80),
          selectedPersona
        );
        activeSessionId = session.id;
        setSessionId(session.id);
        window.localStorage.setItem(SESSION_STORAGE_KEY, String(session.id));
      }

      if (abortController.signal.aborted) {
        throw new DOMException("Chat stopped", "AbortError");
      }

      setMessages((currentMessages) => [
        ...currentMessages,
        { id: userMessageId, role: "user", content: normalizedMessage, sources: [] },
        { id: assistantMessageId, role: "assistant", content: "", sources: [] },
      ]);
      messagesAdded = true;

      for await (const packet of streamSessionMessage(
        activeSessionId,
        normalizedMessage,
        {
           useRag,
          signal: abortController.signal,
        }
      )) {


        if (packet.type === "sources") {
  setMessages((currentMessages) =>
    currentMessages.map((chatMessage) =>
      chatMessage.id === assistantMessageId
        ? {
            ...chatMessage,
            sources: packet.sources,
          }
        : chatMessage
    )
  );
}

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
      if (messagesAdded) {
        setMessages((currentMessages) =>
          currentMessages.filter(
            (chatMessage) =>
              chatMessage.id !== userMessageId &&
              chatMessage.id !== assistantMessageId
          )
        );
      }
      setMessage(normalizedMessage);

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

  function handleNewChat(): void {
    if (isSubmitting || isLoadingHistory) {
      return;
    }

    window.localStorage.removeItem(SESSION_STORAGE_KEY);
    setSessionId(null);
    setSelectedPersona(null);
    setMessages([]);
    setError(null);
  }

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-12 text-slate-100">
      <section className="mx-auto flex min-h-[80vh] max-w-3xl flex-col rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
        <header className="flex items-start justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <h1 className="text-2xl font-semibold">mini-Onyx</h1>
            <p className="mt-1 text-sm text-slate-400">
              {sessionId === null ? "New chat" : `Chat #${sessionId}`}
            </p>
          </div>
          <button
            className="rounded-lg border border-slate-700 px-3 py-2 text-sm hover:bg-slate-800 disabled:opacity-50"
            type="button"
            onClick={handleNewChat}
            disabled={isSubmitting || isLoadingHistory}
          >
            New chat
          </button>
        </header>
        <DocumentUpload
          onUploaded={() => {
              setUseRag(true);
           }}
        />
        <PersonaSelect
          value={selectedPersona}
          onChange={setSelectedPersona}
          disabled={sessionId !== null || isSubmitting || isLoadingHistory}
        />

        <label className="mt-4 flex items-center gap-3 rounded-lg border border-slate-800 bg-slate-950 px-4 py-3">
  <input
    type="checkbox"
    checked={useRag}
    onChange={(event) => setUseRag(event.target.checked)}
    disabled={isSubmitting || isLoadingHistory}
  />
  <span className="text-sm text-slate-300">
    Use uploaded documents (RAG)
  </span>
</label>

        <div
          className="flex flex-1 flex-col gap-4 py-6"
          aria-live="polite"
        >
          {isLoadingHistory ? (
            <p className="text-center text-slate-500">Loading chat history...</p>
          ) : messages.length === 0 ? (
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
                  {chatMessage.sources.length > 0 ? (
  <details className="mt-3 border-t border-slate-700 pt-3 text-sm">
    <summary className="cursor-pointer text-slate-300">
      Sources ({chatMessage.sources.length})
    </summary>

    <ul className="mt-2 space-y-2">
      {chatMessage.sources.map((source) => (
        <li
          key={`${source.document_id}-${source.chunk_id}`}
          className="rounded-lg bg-slate-950 p-3"
        >
          <p className="font-medium text-slate-300">
            Document {source.document_id}, chunk {source.chunk_id}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            Relevance: {source.score.toFixed(3)}
          </p>
          <p className="mt-2 whitespace-pre-wrap text-slate-400">
            {source.content}
          </p>
        </li>
      ))}
    </ul>
  </details>
) : null}
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
            disabled={isSubmitting || isLoadingHistory}
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
              disabled={!message.trim() || isLoadingHistory}
            >
              Send
            </button>
          )}
        </form>
      </section>
    </main>
  );
}
