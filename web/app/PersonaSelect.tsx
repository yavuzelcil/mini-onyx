"use client";

import { formatPersonaName } from "@/lib/personas/format";
import { usePersonas } from "@/lib/personas/hooks";

interface PersonaSelectProps {
  value: string | null;
  onChange: (value: string | null) => void;
  disabled: boolean;
}

export default function PersonaSelect({
  value,
  onChange,
  disabled,
}: PersonaSelectProps) {
  const { data: personas, error, isLoading } = usePersonas();

  if (isLoading) {
    return <p className="mt-4 text-sm text-slate-500">Loading personas...</p>;
  }

  if (error || !personas) {
    return (
      <p className="mt-4 text-sm text-red-300">Could not load personas.</p>
    );
  }

  return (
    <label className="mt-4 flex items-center gap-3 text-sm text-slate-300">
      Persona
      <select
        className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
        value={value ?? ""}
        onChange={(event) => onChange(event.target.value || null)}
        disabled={disabled}
      >
        <option value="">Default</option>
        {personas.map((persona) => (
          <option key={persona.name} value={persona.name}>
            {formatPersonaName(persona.name)}
          </option>
        ))}
      </select>
    </label>
  );
}
