const DEFAULT_API_BASE =
  (typeof process !== 'undefined' && process.env?.EXPO_PUBLIC_API_URL) ||
  'http://localhost:8000';

class GeoSenseApiClient {
  private baseUrl: string = DEFAULT_API_BASE;
  private token: string | null = null;

  setBaseUrl(url: string) {
    this.baseUrl = url.replace(/\/+$/, '');
  }

  setToken(token: string | null) {
    this.token = token;
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
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data?.detail || 'GeoSense API request failed');
    }
    return data as T;
  }

  async login(email: string, password: string) {
    const res = await this.request<{ access_token: string; user: any }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setToken(res.access_token);
    return res;
  }

  async registerCitizen(email: string, password: string, fullName: string, phone?: string) {
    const res = await this.request<{ access_token: string; user: any }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName, phone, role: 'CITIZEN' }),
    });
    this.setToken(res.access_token);
    return res;
  }

  async getCitizenDashboard(latitude = 25.5788, longitude = 91.8933, locationName = 'Shillong, Meghalaya') {
    return this.request<any>(
      `/citizen/dashboard?latitude=${latitude}&longitude=${longitude}&location_name=${encodeURIComponent(locationName)}`
    );
  }

  async getCitizenRisk(latitude: number, longitude: number, locationName?: string) {
    const q = new URLSearchParams({ latitude: String(latitude), longitude: String(longitude) });
    if (locationName) q.set('location_name', locationName);
    return this.request<any>(`/citizen/risk?${q.toString()}`);
  }

  async getNearbyVerifiedResources(latitude: number, longitude: number, radiusKm = 25, resourceType?: string) {
    const q = new URLSearchParams({
      latitude: String(latitude),
      longitude: String(longitude),
      radius_km: String(radiusKm),
    });
    if (resourceType) q.set('resource_type', resourceType);
    return this.request<any>(`/citizen/resources/near?${q.toString()}`);
  }

  async submitIncident(payload: {
    incident_category: string;
    description: string;
    latitude: number;
    longitude: number;
    location_name?: string;
  }) {
    const form = new FormData();
    form.append('incident_category', payload.incident_category);
    form.append('description', payload.description);
    form.append('latitude', String(payload.latitude));
    form.append('longitude', String(payload.longitude));
    if (payload.location_name) form.append('location_name', payload.location_name);

    return this.request<{ incident_id: string; status: string }>('/incidents', {
      method: 'POST',
      body: form,
    });
  }

  async getOfficerDashboard() {
    return this.request<any>('/officer/dashboard');
  }

  async verifyIncident(incidentId: string, status: 'VERIFIED' | 'REJECTED', notes?: string) {
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
    status?: string;
  }) {
    const form = new FormData();
    form.append('latitude', String(payload.latitude));
    form.append('longitude', String(payload.longitude));
    form.append('observations', payload.observations);
    if (payload.location_name) form.append('location_name', payload.location_name);
    if (payload.status) form.append('status', payload.status);

    return this.request<any>('/inspections', {
      method: 'POST',
      body: form,
    });
  }

  async askAgent(message: string, role: 'citizen' | 'field_officer' | 'authority' = 'citizen', sessionId?: string) {
    return this.request<any>('/agent/chat', {
      method: 'POST',
      body: JSON.stringify({ message, role, session_id: sessionId }),
    });
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
