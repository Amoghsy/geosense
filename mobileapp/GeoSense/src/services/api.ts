import Constants from 'expo-constants';
import { Platform } from 'react-native';

function resolveDefaultApiBase(): string {
  const envUrl =
    typeof process !== 'undefined' ? process.env?.EXPO_PUBLIC_API_URL : undefined;
  if (envUrl && envUrl.trim()) {
    return envUrl.trim().replace(/\/+$/, '');
  }

  if (Platform.OS === 'web') {
    if (typeof window !== 'undefined' && window.location?.hostname) {
      return `http://${window.location.hostname}:8000`;
    }
    return 'http://localhost:8000';
  }

  const hostUri =
    Constants.expoConfig?.hostUri ||
    (Constants as any).manifest2?.extra?.expoGo?.debuggerHost ||
    (Constants as any).manifest?.debuggerHost;

  if (typeof hostUri === 'string' && hostUri.length > 0) {
    const host = hostUri.split(':')[0];
    if (host && host !== 'localhost' && host !== '127.0.0.1') {
      return `http://${host}:8000`;
    }
  }

  if (Platform.OS === 'android') {
    return 'http://10.0.2.2:8000';
  }

  return 'http://localhost:8000';
}

const DEFAULT_API_BASE = resolveDefaultApiBase();
const TOKEN_STORAGE_KEY = 'geosense_auth_token';

function readStoredToken(): string | null {
  try {
    if (typeof globalThis !== 'undefined' && (globalThis as any).localStorage) {
      return (globalThis as any).localStorage.getItem(TOKEN_STORAGE_KEY);
    }
  } catch {
    // ignore storage errors
  }
  return null;
}

function writeStoredToken(token: string | null) {
  try {
    if (typeof globalThis !== 'undefined' && (globalThis as any).localStorage) {
      if (token) {
        (globalThis as any).localStorage.setItem(TOKEN_STORAGE_KEY, token);
      } else {
        (globalThis as any).localStorage.removeItem(TOKEN_STORAGE_KEY);
      }
    }
  } catch {
    // ignore storage errors
  }
}

export interface AuthUser {
  user_id: string;
  email: string;
  full_name: string;
  phone?: string | null;
  role: 'CITIZEN' | 'FIELD_OFFICER' | 'AUTHORITY' | 'ADMIN';
  assigned_state?: string | null;
  assigned_district?: string | null;
  officer_code?: string | null;
  is_active?: number;
  created_at?: string;
}

class GeoSenseApiClient {
  private baseUrl: string = DEFAULT_API_BASE;
  private token: string | null = readStoredToken();

  getBaseUrl(): string {
    return this.baseUrl;
  }

  setBaseUrl(url: string) {
    this.baseUrl = url.replace(/\/+$/, '');
  }

  setToken(token: string | null) {
    this.token = token;
    writeStoredToken(token);
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string> | undefined),
    };
    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const res = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers,
    });

    let data: any = null;
    const text = await res.text();
    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      data = { detail: text || 'Invalid server response' };
    }

    if (!res.ok) {
      throw new Error(data?.detail || `GeoSense API request failed (${res.status})`);
    }
    return data as T;
  }

  // ---- Authentication & Profile ----
  async login(identifier: string, password: string) {
    const res = await this.request<{ access_token: string; user: AuthUser }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email: identifier.trim(), password }),
    });
    this.setToken(res.access_token);
    return res;
  }

  async registerCitizen(email: string, password: string, fullName: string, phone?: string) {
    const res = await this.request<{ access_token: string; user: AuthUser }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        email: email.trim(),
        password,
        full_name: fullName.trim(),
        phone: phone?.trim() || undefined,
        role: 'CITIZEN',
      }),
    });
    this.setToken(res.access_token);
    return res;
  }

  async getMe() {
    return this.request<AuthUser>('/users/me');
  }

  async updateMe(payload: { full_name?: string; phone?: string }) {
    return this.request<AuthUser>('/users/me', {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  // ---- Citizen Dashboard, Risk, Weather & XAI ----
  async getCitizenDashboard(
    latitude = 25.2702,
    longitude = 91.7323,
    locationName = 'Cherrapunji, Meghalaya'
  ) {
    return this.request<any>(
      `/citizen/dashboard?latitude=${latitude}&longitude=${longitude}&location_name=${encodeURIComponent(locationName)}`
    );
  }

  async getCitizenRisk(latitude: number, longitude: number, locationName?: string) {
    const q = new URLSearchParams({ latitude: String(latitude), longitude: String(longitude) });
    if (locationName) q.set('location_name', locationName);
    return this.request<any>(`/citizen/risk?${q.toString()}`);
  }

  async getCurrentWeather(latitude: number, longitude: number, locationId?: string) {
    const q = new URLSearchParams({ latitude: String(latitude), longitude: String(longitude) });
    if (locationId) q.set('location_id', locationId);
    return this.request<any>(`/weather/current?${q.toString()}`);
  }

  async getRainfallIndicators(latitude: number, longitude: number, locationId?: string) {
    const q = new URLSearchParams({ latitude: String(latitude), longitude: String(longitude) });
    if (locationId) q.set('location_id', locationId);
    return this.request<any>(`/weather/rainfall?${q.toString()}`);
  }

  async getLatestRisk(locationId: string) {
    return this.request<any>(`/risk/${encodeURIComponent(locationId)}`);
  }

  async getLocationTrends(locationId: string) {
    return this.request<any>(`/risk/${encodeURIComponent(locationId)}/trends`);
  }

  async getRiskExplanation(assessmentId: string) {
    return this.request<any>(`/risk/${encodeURIComponent(assessmentId)}/explanation`);
  }

  async getRiskHotspots(limit = 20) {
    return this.request<any>(`/risk/hotspots?limit=${limit}`);
  }

  // ---- GIS & Mapping ----
  async getGisSummary() {
    return this.request<any>('/gis/summary');
  }

  async getGisLayers() {
    return this.request<any>('/gis/layers');
  }

  async getGisLayerFeatures(layerId: string, region?: string, limit = 50) {
    const q = new URLSearchParams({ limit: String(limit) });
    if (region) q.set('region', region);
    return this.request<any>(`/gis/layers/${encodeURIComponent(layerId)}/features?${q.toString()}`);
  }

  async getGisHotspots(state?: string, limit = 20) {
    const q = new URLSearchParams({ limit: String(limit) });
    if (state) q.set('state', state);
    return this.request<any>(`/gis/hotspots?${q.toString()}`);
  }

  // ---- Nearby Resources ----
  async getNearbyVerifiedResources(
    latitude: number,
    longitude: number,
    radiusKm = 50,
    resourceType?: string
  ) {
    const q = new URLSearchParams({
      latitude: String(latitude),
      longitude: String(longitude),
      radius_km: String(radiusKm),
    });
    if (resourceType) q.set('resource_type', resourceType);
    return this.request<any>(`/citizen/resources/near?${q.toString()}`);
  }

  // ---- Incidents ----
  async submitIncident(payload: {
    incident_category: string;
    description: string;
    latitude: number;
    longitude: number;
    location_name?: string;
    state?: string;
    district?: string;
    incident_time?: string;
    contact_info?: string;
  }) {
    const form = new FormData();
    form.append('incident_category', payload.incident_category);
    form.append('description', payload.description);
    form.append('latitude', String(payload.latitude));
    form.append('longitude', String(payload.longitude));
    if (payload.location_name) form.append('location_name', payload.location_name);
    if (payload.state) form.append('state', payload.state);
    if (payload.district) form.append('district', payload.district);
    if (payload.incident_time) form.append('incident_time', payload.incident_time);
    if (payload.contact_info) form.append('contact_info', payload.contact_info);

    return this.request<{ success: boolean; incident_id: string; status: string; created_at: string }>(
      '/incidents',
      { method: 'POST', body: form }
    );
  }

  async getMyReports() {
    return this.request<{ count: number; incidents: any[] }>('/incidents/my-reports');
  }

  // ---- Field Officer Workflows ----
  async getOfficerDashboard() {
    return this.request<any>('/officer/dashboard');
  }

  async getOfficerIncidents(status?: string, state?: string) {
    const q = new URLSearchParams();
    if (status) q.set('status', status);
    if (state) q.set('state', state);
    const suffix = q.toString() ? `?${q.toString()}` : '';
    return this.request<{ count: number; jurisdiction_state?: string; incidents: any[] }>(
      `/officer/incidents${suffix}`
    );
  }

  async getOfficerAssignments() {
    return this.request<any>('/officer/assignments');
  }

  async verifyIncident(
    incidentId: string,
    status: 'VERIFIED' | 'REJECTED' | 'NEEDS_INFO',
    notes?: string
  ) {
    return this.request<any>(`/incidents/${incidentId}/verify`, {
      method: 'POST',
      body: JSON.stringify({ status, verification_notes: notes }),
    });
  }

  async submitInspection(payload: {
    latitude: number;
    longitude: number;
    observations: string;
    location_name?: string;
    state?: string;
    district?: string;
    status?: 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED' | 'NEEDS_FOLLOW_UP';
    inspection_notes?: string;
    follow_up_required?: boolean;
  }) {
    const form = new FormData();
    form.append('latitude', String(payload.latitude));
    form.append('longitude', String(payload.longitude));
    form.append('observations', payload.observations);
    if (payload.location_name) form.append('location_name', payload.location_name);
    if (payload.state) form.append('state', payload.state);
    if (payload.district) form.append('district', payload.district);
    if (payload.status) form.append('status', payload.status);
    if (payload.inspection_notes) form.append('inspection_notes', payload.inspection_notes);
    if (payload.follow_up_required !== undefined) {
      form.append('follow_up_required', String(payload.follow_up_required));
    }

    return this.request<{ success: boolean; inspection_id: string; status: string; created_at: string }>(
      '/inspections',
      { method: 'POST', body: form }
    );
  }

  async getInspections(state?: string) {
    const q = state ? `?state=${encodeURIComponent(state)}` : '';
    return this.request<{ count: number; inspections: any[] }>(`/inspections${q}`);
  }

  async updateInspection(
    inspectionId: string,
    payload: {
      status?: 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED' | 'NEEDS_FOLLOW_UP';
      observations?: string;
      inspection_notes?: string;
      follow_up_required?: boolean;
    }
  ) {
    return this.request<any>(`/inspections/${encodeURIComponent(inspectionId)}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  // ---- AI Agent ----
  async askAgent(
    message: string,
    role: 'citizen' | 'field_officer' | 'authority' = 'citizen',
    sessionId?: string
  ) {
    return this.request<any>('/agent/chat', {
      method: 'POST',
      body: JSON.stringify({ message, role, session_id: sessionId }),
    });
  }

  // ---- Alerts & Notifications ----
  async getAlerts(params?: { severity?: string; state?: string; limit?: number }) {
    const q = new URLSearchParams();
    if (params?.severity) q.set('severity', params.severity);
    if (params?.state) q.set('state', params.state);
    if (params?.limit) q.set('limit', String(params.limit));
    const suffix = q.toString() ? `?${q.toString()}` : '';
    return this.request<{ count: number; alerts: any[] }>(`/alerts${suffix}`);
  }

  async getNotifications(unreadOnly = false) {
    return this.request<{ count: number; notifications: any[] }>(
      `/notifications?unread_only=${unreadOnly}`
    );
  }

  async markNotificationRead(notificationId: string) {
    return this.request<any>(`/notifications/${notificationId}/read`, { method: 'PATCH' });
  }

  async acknowledgeAlert(alertId: string) {
    return this.request<any>(`/alerts/${alertId}/acknowledge`, { method: 'POST' });
  }

  async registerFcmDevice(fcmToken: string, platform: 'android' | 'ios' | 'web' = 'android') {
    return this.request<{ device_id: string }>('/notifications/devices/register', {
      method: 'POST',
      body: JSON.stringify({ fcm_token: fcmToken, platform }),
    });
  }

  async unregisterFcmDevice(deviceId: string) {
    return this.request<any>(`/notifications/devices/${deviceId}`, { method: 'DELETE' });
  }

  async updateNotificationPreferences(prefs: {
    email_enabled?: boolean;
    push_enabled?: boolean;
    preferred_state?: string;
  }) {
    return this.request<any>('/notifications/preferences', {
      method: 'PATCH',
      body: JSON.stringify(prefs),
    });
  }
}

export const geoSenseApi = new GeoSenseApiClient();
