const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface BirthDetails {
  date: string;
  time: string;
  latitude: number;
  longitude: number;
  timezone_offset_hours: number;
}

export interface PlanetPosition {
  planet: string;
  longitude_degrees: number;
  sign: string;
  house: number;
  nakshatra: string;
  nakshatra_pada: number;
  is_retrograde: boolean;
}

export interface DashaPeriod {
  lord: string;
  start_date: string;
  end_date: string;
  level: number;
}

export interface PanchangDay {
  date: string;
  tithi: string;
  nakshatra: string;
  yoga: string;
  karana: string;
  moon_sign: string;
  sun_sign: string;
}

export interface ComputedChart {
  birth_details: BirthDetails;
  computed_at: string;
  positions: PlanetPosition[];
  current_dashas: DashaPeriod[];
  panchang_today: PanchangDay;
}

export type ClaimStatus = "grounded" | "ungrounded" | "unverifiable";

export interface VerifiedClaim {
  claim: { text: string; source_model: string };
  status: ClaimStatus;
  grounded_field_path: string | null;
  confidence: number;
}

export interface GenerationResult {
  chart_id: string;
  model_used: string;
  narrative: string;
  claims: VerifiedClaim[];
  hallucination_rate: number;
}

export interface EvalCase {
  birth_details: BirthDetails;
  ungrounded_result: GenerationResult;
  grounded_result: GenerationResult;
}

export interface EvalReport {
  provider: string;
  cases: EvalCase[];
  avg_ungrounded_hallucination_rate: number;
  avg_grounded_hallucination_rate: number;
  relative_reduction: number;
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API error ${res.status} on ${path}: ${text}`);
  }
  return res.json();
}

export const api = {
  computeChart: (birth: BirthDetails) =>
    apiFetch<ComputedChart>("/api/charts/compute", {
      method: "POST",
      body: JSON.stringify(birth),
    }),

  todaysPanchang: () => apiFetch<PanchangDay>("/api/charts/panchang/today"),

  generateNarrative: (birth: BirthDetails, provider: "groq" | "gemini" = "groq") =>
    apiFetch<GenerationResult>(`/api/generate/narrative?provider=${provider}`, {
      method: "POST",
      body: JSON.stringify(birth),
    }),

  runEval: (provider: "groq" | "gemini" = "groq") =>
    apiFetch<EvalReport>(`/api/eval/run?provider=${provider}`, {
      method: "POST",
    }),
};
