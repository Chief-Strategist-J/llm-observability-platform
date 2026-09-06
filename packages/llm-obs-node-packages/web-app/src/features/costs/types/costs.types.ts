export interface CostSummaryResult {
  total_cost_usd: number;           // e.g. 1420.50
  daily_avg_usd: number;            // e.g. 47.35
  cost_delta_pct: number;           // e.g. +5.8
  projected_monthly_usd: number;    // e.g. 1450.00
}

export interface CostByProvider {
  provider: string;                 // e.g. "OpenAI", "Anthropic", "Cohere"
  model: string;                    // e.g. "gpt-4o", "claude-3-5-sonnet"
  cost_usd: number;
  token_count: number;
  pct_of_total: number;
}

export interface TokenConsumptionPoint {
  date: string;
  input_tokens: number;
  output_tokens: number;
  total_cost_usd: number;
}
