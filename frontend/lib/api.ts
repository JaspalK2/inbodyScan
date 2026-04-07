/**
 * Typed API client for all microservices.
 */

const URLS = {
  auth: process.env.NEXT_PUBLIC_AUTH_URL ?? "http://localhost:8001",
  user: process.env.NEXT_PUBLIC_USER_URL ?? "http://localhost:8002",
  scan: process.env.NEXT_PUBLIC_SCAN_URL ?? "http://localhost:8003",
  analytics: process.env.NEXT_PUBLIC_ANALYTICS_URL ?? "http://localhost:8004",
  recommendation: process.env.NEXT_PUBLIC_RECOMMENDATION_URL ?? "http://localhost:8005",
  admin: process.env.NEXT_PUBLIC_ADMIN_URL ?? "http://localhost:8006",
};

let _accessToken: string | null = null;
export function setAccessToken(t: string) { _accessToken = t; }
export function clearAccessToken() { _accessToken = null; }
export function getAccessToken() { return _accessToken; }

let _onSessionExpired: (() => void) | null = null;
export function registerSessionExpiredHandler(handler: () => void) { _onSessionExpired = handler; }

async function _doFetch<T>(base: keyof typeof URLS, path: string, options: RequestInit): Promise<T> {
  const headers: Record<string, string> = { ...(options.headers as Record<string, string>) };
  if (_accessToken) headers["Authorization"] = `Bearer ${_accessToken}`;
  if (!(options.body instanceof FormData)) headers["Content-Type"] = "application/json";
  const res = await fetch(`${URLS[base]}${path}`, { ...options, headers, credentials: "include" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw { status: res.status, detail: err.detail ?? "Request failed" };
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

async function request<T>(base: keyof typeof URLS, path: string, options: RequestInit = {}): Promise<T> {
  try {
    return await _doFetch<T>(base, path, options);
  } catch (err: unknown) {
    const e = err as { status?: number };
    if (e?.status !== 401) throw err;

    // First 401 — attempt silent token refresh
    try {
      const { access_token } = await _doFetch<{ access_token: string }>("auth", "/api/auth/refresh", { method: "POST" });
      setAccessToken(access_token);
      return await _doFetch<T>(base, path, options);
    } catch {
      // Refresh failed or second 401 — session fully expired
      clearAccessToken();
      if (_onSessionExpired) _onSessionExpired();
      throw { status: 401, detail: "Your session has expired. Please log in again." };
    }
  }
}

// ── Auth ──────────────────────────────────────────────────────────────────────
export interface GoogleLoginResponse {
  access_token?: string;
  token_type?: string;
  link_token?: string;
  email?: string;
  google_name?: string;
}

export const auth = {
  login: (username: string, password: string) =>
    request<{ access_token: string }>("auth", "/api/auth/login", { method: "POST", body: JSON.stringify({ username, password }) }),
  register: (username: string, email: string, password: string) =>
    request<{ id: string; username: string; email: string }>("auth", "/api/auth/register", { method: "POST", body: JSON.stringify({ username, email, password }) }),
  refresh: () => request<{ access_token: string }>("auth", "/api/auth/refresh", { method: "POST" }),
  logout: () => request("auth", "/api/auth/logout", { method: "POST" }),
  me: () => request<{ id: string; username: string; email: string; is_admin: boolean; google_sub?: string }>("auth", "/api/auth/me"),
  googleLogin: (idToken: string) =>
    request<GoogleLoginResponse>("auth", "/api/auth/google", { method: "POST", body: JSON.stringify({ id_token: idToken }) }),
  confirmGoogleLink: (linkToken: string) =>
    request<{ access_token: string }>("auth", "/api/auth/google/confirm-link", { method: "POST", body: JSON.stringify({ link_token: linkToken }) }),
};

// ── User ──────────────────────────────────────────────────────────────────────
export const user = {
  getProfile: () => request<UserProfile>("user", "/api/users/me/profile"),
  updateProfile: (data: Partial<UserProfile>) =>
    request<UserProfile>("user", "/api/users/me/profile", { method: "PATCH", body: JSON.stringify(data) }),
  getGoal: () => request<HealthGoal | null>("user", "/api/users/me/goal"),
  setGoal: (goal_type: string) =>
    request<HealthGoal>("user", "/api/users/me/goal", { method: "PUT", body: JSON.stringify({ goal_type }) }),
  getDietaryRestrictions: () => request<DietaryRestriction[]>("user", "/api/users/me/dietary-restrictions"),
  addRestriction: (restriction_type: string, notes?: string) =>
    request<DietaryRestriction>("user", "/api/users/me/dietary-restrictions", { method: "POST", body: JSON.stringify({ restriction_type, notes }) }),
  removeRestriction: (id: string) =>
    request("user", `/api/users/me/dietary-restrictions/${id}`, { method: "DELETE" }),
};

// ── Scans ─────────────────────────────────────────────────────────────────────
export const scans = {
  upload: (file: File, scan_date: string) => {
    const form = new FormData(); form.append("file", file); form.append("scan_date", scan_date);
    return request<ScanWithMetrics>("scan", "/api/scans/upload", { method: "POST", body: form });
  },
  uploadCsv: (file: File, scan_date?: string) => {
    const form = new FormData(); form.append("file", file);
    if (scan_date) form.append("scan_date", scan_date);
    return request<ScanWithMetrics>("scan", "/api/scans/upload-csv", { method: "POST", body: form });
  },
  list: () => request<Scan[]>("scan", "/api/scans"),
  get: (id: string) => request<ScanWithMetrics>("scan", `/api/scans/${id}`),
  downloadUrl: (id: string) => request<{ url: string }>("scan", `/api/scans/${id}/download-url`),
};

// ── Analytics ─────────────────────────────────────────────────────────────────
export const analytics = {
  dashboard: () => request<DashboardResponse>("analytics", "/api/analytics/dashboard"),
};

// ── Recommendations ───────────────────────────────────────────────────────────
export const recommendations = {
  // Macros
  calculateMacros: (data: { metrics: Record<string, number | null>; goal_type: string; age?: number; height_cm?: number; gender?: string; activity_level?: string }) =>
    request<MacroTargets>("recommendation", "/api/recommendations/diet/macros", { method: "POST", body: JSON.stringify(data) }),
  // Exercise search (CC0 dataset)
  searchExercises: (q: string, limit = 20) =>
    request<ExerciseSearchResult[]>("recommendation", `/api/recommendations/exercises/search?q=${encodeURIComponent(q)}&limit=${limit}`),
  // Food search
  searchFood: (q: string, page_size = 25) =>
    request<FoodResult[]>("recommendation", `/api/recommendations/food/search?q=${encodeURIComponent(q)}&page_size=${page_size}`),
  getFood: (fdc_id: number) =>
    request<FoodResult>("recommendation", `/api/recommendations/food/${fdc_id}`),
  // Custom meals
  createMeal: (data: CustomMealCreate) =>
    request<CustomMealOut>("recommendation", "/api/recommendations/meals", { method: "POST", body: JSON.stringify(data) }),
  listMeals: () => request<CustomMealOut[]>("recommendation", "/api/recommendations/meals"),
  getMeal: (id: string) => request<CustomMealOut>("recommendation", `/api/recommendations/meals/${id}`),
  updateMeal: (id: string, data: Partial<CustomMealCreate>) =>
    request<CustomMealOut>("recommendation", `/api/recommendations/meals/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteMeal: (id: string) =>
    request("recommendation", `/api/recommendations/meals/${id}`, { method: "DELETE" }),
  // Day plans
  createDayPlan: (data: DayPlanCreate) =>
    request<DayPlanOut>("recommendation", "/api/recommendations/day-plans", { method: "POST", body: JSON.stringify(data) }),
  listDayPlans: () => request<DayPlanOut[]>("recommendation", "/api/recommendations/day-plans"),
  deleteDayPlan: (id: string) =>
    request("recommendation", `/api/recommendations/day-plans/${id}`, { method: "DELETE" }),
  // Workout splits
  createSplit: (data: WorkoutSplitCreate) =>
    request<WorkoutSplitOut>("recommendation", "/api/recommendations/splits", { method: "POST", body: JSON.stringify(data) }),
  listSplits: () => request<WorkoutSplitOut[]>("recommendation", "/api/recommendations/splits"),
  getSplit: (id: string) => request<WorkoutSplitOut>("recommendation", `/api/recommendations/splits/${id}`),
  scoreSplit: (data: WorkoutSplitCreate) =>
    request<WorkoutScore>("recommendation", "/api/recommendations/splits/score", { method: "POST", body: JSON.stringify(data) }),
  deleteSplit: (id: string) =>
    request("recommendation", `/api/recommendations/splits/${id}`, { method: "DELETE" }),
  // LLM plans
  generateDiet: (data: { scan_id: string; metrics: Record<string, number | null>; goal_type: string; dietary_restrictions: string[]; age?: number; height_cm?: number; gender?: string; activity_level?: string }) =>
    request<DietRecommendation>("recommendation", "/api/recommendations/diet/generate", { method: "POST", body: JSON.stringify(data) }),
  editDietPlan: (id: string, edited_plan: Record<string, unknown>) =>
    request<DietRecommendation>("recommendation", `/api/recommendations/diet/${id}`, { method: "PATCH", body: JSON.stringify({ edited_plan }) }),
  listDiet: () => request<DietRecommendation[]>("recommendation", "/api/recommendations/diet"),
  deleteDiet: (id: string) =>
    request("recommendation", `/api/recommendations/diet/${id}`, { method: "DELETE" }),
  generateWorkout: (data: { scan_id: string; metrics: Record<string, number | null>; goal_type: string }) =>
    request<WorkoutRecommendation>("recommendation", "/api/recommendations/workout/generate", { method: "POST", body: JSON.stringify(data) }),
  editWorkoutPlan: (id: string, edited_plan: Record<string, unknown>) =>
    request<WorkoutRecommendation>("recommendation", `/api/recommendations/workout/${id}`, { method: "PATCH", body: JSON.stringify({ edited_plan }) }),
  listWorkout: () => request<WorkoutRecommendation[]>("recommendation", "/api/recommendations/workout"),
  deleteWorkout: (id: string) =>
    request("recommendation", `/api/recommendations/workout/${id}`, { method: "DELETE" }),
  scoreGeneratedPlan: (plan: Record<string, unknown>) =>
    request<WorkoutScore>("recommendation", "/api/recommendations/workout/score-plan", { method: "POST", body: JSON.stringify({ plan }) }),
  // Food log
  createFoodLog: (data: FoodLogBatchCreate) =>
    request<FoodLogEntryOut[]>("recommendation", "/api/recommendations/food-log", { method: "POST", body: JSON.stringify(data) }),
  getFoodLog: (date: string) =>
    request<FoodLogEntryOut[]>("recommendation", `/api/recommendations/food-log?date=${date}`),
  deleteFoodLogEntry: (id: string) =>
    request<void>("recommendation", `/api/recommendations/food-log/${id}`, { method: "DELETE" }),
  getFoodLogDates: () =>
    request<string[]>("recommendation", "/api/recommendations/food-log/dates"),
};

// ── Admin ─────────────────────────────────────────────────────────────────────
export const admin = {
  listUsers: () => request<AdminUser[]>("admin", "/api/admin/users"),
  createUser: (data: { username: string; email: string; password: string; is_admin: boolean }) =>
    request<AdminUser>("admin", "/api/admin/users", { method: "POST", body: JSON.stringify(data) }),
  toggleActive: (user_id: string, is_active: boolean) =>
    request<AdminUser>("admin", `/api/admin/users/${user_id}`, { method: "PATCH", body: JSON.stringify({ is_active }) }),
};

// ── Types ─────────────────────────────────────────────────────────────────────
export interface UserProfile { id: string; user_id: string; first_name: string | null; last_name: string | null; age: number | null; height_cm: number | null; weight_kg: number | null; gender: string | null; activity_level: string | null; }
export interface HealthGoal { id: string; user_id: string; goal_type: string; }
export interface DietaryRestriction { id: string; user_id: string; restriction_type: string; notes: string | null; }
export interface Scan { id: string; user_id: string; scan_date: string; storage_path: string; created_at: string; }
export interface Metric { metric_key: string; metric_value: number | null; }
export interface ScanWithMetrics { scan: Scan; metrics: Metric[]; }
export interface DeltaCard { metric_key: string; current_value: number | null; previous_value: number | null; delta: number | null; delta_pct: number | null; }
export interface MetricPoint { scan_date: string; value: number | null; }
export interface MetricHistory { metric_key: string; points: MetricPoint[]; }
export interface DashboardResponse { user_id: string; latest_scan_date: string | null; previous_scan_date: string | null; deltas: DeltaCard[]; history: MetricHistory[]; }

export interface MacroTargets { calories: number; protein_g: number; carbs_g: number; fat_g: number; fiber_g: number; bmr: number; tdee: number; goal_adjustment_kcal: number; protein_ratio: string; notes: string; }
export interface ExerciseSearchResult { name: string; primary_muscles: string[]; secondary_muscles: string[]; category: string; equipment: string; level: string; }
export interface FoodResult { fdc_id: number; name: string; brand: string | null; category: string | null; calories_kcal: number | null; protein_g: number | null; carbs_g: number | null; fat_g: number | null; fiber_g: number | null; sugar_g: number | null; sodium_mg: number | null; potassium_mg: number | null; calcium_mg: number | null; iron_mg: number | null; vitamin_c_mg: number | null; vitamin_d_ug: number | null; serving_size: number | null; serving_unit: string | null; }
export interface MealItem { id?: string; fdc_id?: number | null; food_name: string; quantity_g: number; entered_quantity?: number | null; entered_unit?: string | null; calories_kcal?: number | null; protein_g?: number | null; carbs_g?: number | null; fat_g?: number | null; fiber_g?: number | null; sodium_mg?: number | null; }
export interface CustomMealOut { id: string; user_id: string; name: string; description: string | null; items: MealItem[]; created_at: string; updated_at: string; }
export interface CustomMealCreate { name: string; description?: string; items: MealItem[]; }
export interface DayPlanEntry { id?: string; meal_slot: string; custom_meal_id?: string | null; custom_meal_name?: string | null; calories_kcal?: number | null; protein_g?: number | null; carbs_g?: number | null; fat_g?: number | null; fiber_g?: number | null; items_snapshot?: MealItem[] | null; }
export interface DayPlanOut { id: string; user_id: string; name: string; plan_date: string | null; notes: string | null; entries: DayPlanEntry[]; created_at: string; updated_at: string; }
export interface DayPlanCreate { name: string; plan_date?: string; notes?: string; entries: DayPlanEntry[]; }
export interface Exercise { exercise_name: string; sets?: number | null; reps?: string | null; weight_kg?: number | null; rest_seconds?: number | null; notes?: string | null; }
export interface SplitDay { day_label: string; focus?: string | null; is_rest?: boolean; exercises?: Exercise[]; }
export interface WorkoutScore { overall: number; coverage_score: number; volume_score: number; balance_score: number; cardio_score: number; frequency_score: number; covered_groups: string[]; missing_groups: string[]; weekly_sets_per_group: Record<string, number>; feedback: string[]; label: string; }
export interface WorkoutSplitOut { id: string; user_id: string; name: string; description: string | null; days: (SplitDay & { id: string; exercises: (Exercise & { id: string })[]; })[]; score: WorkoutScore | null; created_at: string; updated_at: string; }
export interface WorkoutSplitCreate { name: string; description?: string; days: SplitDay[]; }
export interface DietRecommendation { id: string; user_id: string; scan_id: string; goal_type: string; structured_plan: Record<string, unknown>; edited_plan: Record<string, unknown> | null; created_at: string; }
export interface WorkoutRecommendation { id: string; user_id: string; scan_id: string; goal_type: string; structured_plan: Record<string, unknown>; edited_plan: Record<string, unknown> | null; created_at: string; }
export interface AdminUser { id: string; username: string; email: string; is_admin: boolean; is_active: boolean; }

export interface FoodLogEntryIn {
  fdc_id?: number | null;
  food_name: string;
  brand?: string | null;
  source?: string;
  source_ref_id?: string | null;
  quantity_g: number;
  entered_quantity?: number | null;
  entered_unit?: string | null;
  calories_kcal?: number | null;
  protein_g?: number | null;
  carbs_g?: number | null;
  fat_g?: number | null;
  fiber_g?: number | null;
}

export interface FoodLogEntryOut extends FoodLogEntryIn {
  id: string;
  user_id: string;
  log_date: string;
  created_at: string;
}

export interface FoodLogBatchCreate {
  log_date: string;
  entries: FoodLogEntryIn[];
}
