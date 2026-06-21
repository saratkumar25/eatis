export type Role = "viewer" | "analyst" | "operator" | "admin";

export type Severity = "low" | "medium" | "high" | "critical";

export type EventStatus = "scheduled" | "active" | "completed" | "cancelled";

export type EventType =
  | "rally"
  | "festival"
  | "sports"
  | "construction"
  | "parade"
  | "marathon"
  | "concert"
  | "other";

export interface User {
  id: number | string;
  name: string;
  email: string;
  role: Role;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user?: User;
}

// Matches backend EventResponse exactly
export interface EventItem {
  id: number;
  name: string;
  description?: string | null;
  event_type: EventType | string;
  location_name: string;
  address?: string | null;
  latitude: number;
  longitude: number;
  start_datetime: string;
  end_datetime: string;
  duration_hours: number;
  expected_crowd_size: number;
  has_road_closure: boolean;          // backend field name
  road_closure_details?: string | null;
  status: EventStatus;
  created_by?: number;
  created_at?: string;
  updated_at?: string;
}

// Matches backend PredictionResponse exactly
export interface Prediction {
  id?: number;
  event_id: number;
  congestion_level: Severity;
  risk_score: number;
  delay_time_minutes: number;         // backend field name
  impact_radius_km: number;
  traffic_volume_increase_pct?: number;
  confidence_score: number;
  model_version?: string;
  created_at?: string;
}

// Matches backend ResourceResponse exactly
export interface ResourceAllocation {
  id?: number;
  event_id: number;
  officers_required: number;          // backend field name
  barricades_required: number;        // backend field name
  patrol_vehicles: number;
  emergency_units: number;
  tow_vehicles: number;
  deployment_notes?: string | null;
  created_at?: string;
}

// Matches backend RouteResponse exactly
export interface RouteSuggestion {
  id?: number;
  event_id: number;
  route_type: string;
  route_name: string;                 // backend field name
  description?: string | null;
  geojson_coordinates?: string | null; // backend sends JSON string
  distance_km?: number | null;
  estimated_time_minutes?: number | null;
  diversion_benefit?: string | null;  // backend field name
  created_at?: string;
}

export interface HeatmapPoint {
  lat: number;
  lng: number;
  intensity: number;
}

export interface HeatmapResponse {
  event_id: number;
  points: HeatmapPoint[];
  congestion_level: string;
  risk_score: number;
  impact_radius_km: number;
  zones: { name?: string; level?: Severity; [key: string]: any }[];
}

// Matches backend AnalyticsDashboard exactly
export interface AnalyticsSummary {
  total_events: number;
  active_events: number;
  completed_events: number;
  scheduled_events: number;
  cancelled_events: number;
  events_by_type: Record<string, number>;
  congestion_distribution: Record<string, number>;
  high_risk_events: number;
  avg_risk_score: number;
  avg_prediction_accuracy?: number | null;
  total_officers_deployed: number;
  total_resources_allocated: Record<string, number>;
}

export interface TrendPoint {
  period: string;
  event_count: number;
  avg_risk_score: number;
}

export interface HighRiskZone {
  location_name: string;              // backend field name
  latitude: number;
  longitude: number;
  event_count: number;
  avg_risk_score: number;             // backend field name
}

export interface AnalyticsDashboard {
  summary: AnalyticsSummary;
  trends: TrendPoint[];
  high_risk_zones: HighRiskZone[];
}

// Matches backend PostEventResponse exactly
export interface PostEventAnalysis {
  id?: number;
  event_id: number;
  predicted_congestion_level: Severity;
  predicted_risk_score: number;
  predicted_delay_minutes: number;
  actual_congestion_level: Severity;
  actual_risk_score?: number | null;
  actual_delay_minutes?: number | null;
  actual_crowd_size?: number | null;
  prediction_accuracy_pct?: number | null;  // backend field name
  congestion_match?: boolean | null;
  performance_notes?: string | null;
  improvement_recommendations?: string | null; // backend field name
  analyzed_at?: string;
}

// Matches backend CopilotResponse exactly
export interface CopilotMessage {
  query_id?: number;                  // backend field name
  user_query: string;                 // backend field name
  gemini_response: string;            // backend field name
  event_id?: number | null;
  created_at?: string;
}

// Events list response from backend: { total, skip, limit, data: [...] }
export interface PaginatedEvents {
  data: EventItem[];                  // backend uses "data" not "items"
  total: number;
  skip: number;
  limit: number;
}
