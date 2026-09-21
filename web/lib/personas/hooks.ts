import useSWR from "swr";

import { fetchPersonas } from "@/lib/chat";
import type { Persona } from "@/lib/chat";

const PERSONAS_KEY = "/api/chat/personas";

export function usePersonas() {
  return useSWR<Persona[], Error>(PERSONAS_KEY, fetchPersonas, {
    revalidateOnFocus: false,
  });
}
