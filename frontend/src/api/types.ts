// Auth
export interface UserResponse {
  id: string
  username: string
  email: string | null
  phone: string | null
  created_at: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user_id: string
}

// Risk Assessment
export interface RiskProfileResponse {
  has_profile: boolean
  has_assessment: boolean
  profile: {
    lifecycle_stage: string | null
    risk_capacity: string | null
    investable_assets: number | null
    monthly_surplus: number | null
  }
  latest_assessment: {
    score: number
    risk_level: string
    assessed_at: string
  } | null
}

// Orchestrator
export interface FourBucketItem {
  allocation: number
  products: string[]
  reason: string
}

export interface FourBuckets {
  living_money: FourBucketItem
  stable_money: FourBucketItem
  growth_money: FourBucketItem
  protection_money: FourBucketItem
}

export interface StressTestItem {
  loss: number
  recovery_time: string
}

export interface StrategyResult {
  four_buckets: FourBuckets
  rebalance_triggers: { drift_threshold: number; review_frequency: string }
  stress_test: Record<string, StressTestItem>
}

export interface CoachingEntry {
  type: string
  message: string
  action: string
}

export interface OrchestratorStatusResponse {
  user_id: string
  current_step: string
  user_profile: Record<string, any> | null
  market_analysis: Record<string, any> | null
  strategy: StrategyResult | null
  coaching_history: CoachingEntry[] | null
  error: string | null
}
