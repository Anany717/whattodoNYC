import type { RecommendationRequest, RecommendationResponse } from "@/lib/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function fetchRecommendations(
  payload: RecommendationRequest
): Promise<RecommendationResponse> {
  const response = await fetch(`${BASE_URL}/recommendations`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || "Failed to load recommendations");
  }

  return response.json();
}

export async function authRequest(path: string, payload: Record<string, unknown>) {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const body = await response.json();
  if (!response.ok) {
    throw new Error(body.detail || "Authentication request failed");
  }
  return body;
}
