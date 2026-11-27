import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { geoSenseApi, AuthUser } from '../services/api';

export type UserRole = 'citizen' | 'officer';

export type ScreenName =
  // Auth / Portal screens
  | 'login-portal'
  // Citizen screens
  | 'citizen-home'
  | 'safety-outlook'
  | 'map'
  | 'location-details'
  | 'understand-risk'
  | 'evacuation'
  | 'resources'
  | 'report-incident-1'
  | 'report-incident-2'
  | 'report-incident-success'
  | 'alerts'
  | 'profile'
  | 'offline-maps'
  // Field Officer screens
  | 'officer-login'
  | 'officer-home'
  | 'officer-mission'
  | 'officer-verification'
  | 'officer-report'
  | 'officer-alerts'
  | 'officer-offline'
  | 'officer-profile';

export type TabName = 'home' | 'map' | 'missions' | 'alerts' | 'profile';

export interface SelectedLocation {
  name: string;
  latitude: number;
  longitude: number;
  locationId?: string;
}

export interface IncidentReportDraft {
  type: string;
  location: string;
  latitude: number;
  longitude: number;
  coords: string;
  accuracy: string;
  description: string;
  photoUri?: string;
  time?: string;
  severity: 'Low' | 'Moderate' | 'High' | 'Critical';
  accessibility: string;
  peopleAffected: string;
  referenceId?: string;
}

export interface VerificationReport {
  id: string;
  title: string;
  category: string;
  location: string;
  latitude: number;
  longitude: number;
  timeAgo: string;
  quote: string;
  submitter: string;
  severity: 'High' | 'Moderate';
  status: 'pending' | 'verified' | 'rejected';
}

function formatCoords(lat: number, lon: number): string {
  const latDir = lat >= 0 ? 'N' : 'S';
  const lonDir = lon >= 0 ? 'E' : 'W';
  return `${Math.abs(lat).toFixed(4)}° ${latDir}, ${Math.abs(lon).toFixed(4)}° ${lonDir}`;
}

export function formatRelativeTime(iso?: string | null): string {
  if (!iso) return 'Recently';
  const dt = new Date(iso);
  if (Number.isNaN(dt.getTime())) return 'Recently';
  const diffSec = Math.max(0, Math.floor((Date.now() - dt.getTime()) / 1000));
  if (diffSec < 60) return 'Just now';
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin} min ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr} hr ago`;
  const diffDay = Math.floor(diffHr / 24);
  return `${diffDay}d ago`;
}

const DEFAULT_LOCATION: SelectedLocation = {
  name: 'Cherrapunji, Meghalaya',
  latitude: 25.2702,
  longitude: 91.7323,
};

function createDefaultDraft(loc: SelectedLocation = DEFAULT_LOCATION): IncidentReportDraft {
  return {
    type: 'Landslide',
    location: loc.name,
    latitude: loc.latitude,
    longitude: loc.longitude,
    coords: formatCoords(loc.latitude, loc.longitude),
    accuracy: '±5 m',
    description: '',
    time: new Date().toISOString(),
    severity: 'High',
    accessibility: 'Partially blocked',
    peopleAffected: 'Not known',
  };
}

interface AppContextType {
  role: UserRole;
  setRole: (role: UserRole) => void;
  portalTab: 'citizen' | 'officer';
  setPortalTab: (tab: 'citizen' | 'officer') => void;
  currentScreen: ScreenName;
  activeTab: TabName;
  navigate: (screen: ScreenName) => void;
  goBack: () => void;
  canGoBack: boolean;

  selectedLocation: SelectedLocation;
  setSelectedLocation: (loc: SelectedLocation) => void;
  latestAssessmentId: string | null;
  setLatestAssessmentId: (id: string | null) => void;

  incidentDraft: IncidentReportDraft;
  updateIncidentDraft: (data: Partial<IncidentReportDraft>) => void;
  resetIncidentDraft: () => void;
  submitIncidentToBackend: () => Promise<string>;

  verificationReports: VerificationReport[];
  refreshOfficerIncidents: () => Promise<void>;
  verifyReport: (id: string, notes?: string) => Promise<void>;
  rejectReport: (id: string, notes?: string) => Promise<void>;

  currentUser: AuthUser | null;
  isRestoringSession: boolean;
  isLoggedInCitizen: boolean;
  isLoggedInOfficer: boolean;
  citizenName: string;
  citizenPhone: string;
  officerId: string;

  loginCitizen: (identifier: string, password: string) => Promise<void>;
  registerCitizen: (fullName: string, email: string, phone: string, password: string) => Promise<void>;
  logoutCitizen: () => void;
  loginOfficer: (identifier: string, password: string) => Promise<void>;
  logoutOfficer: () => void;
  updateUserProfile: (fullName: string, phone: string) => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [role, setRole] = useState<UserRole>('citizen');
  const [portalTab, setPortalTab] = useState<'citizen' | 'officer'>('citizen');
  const [currentScreen, setCurrentScreen] = useState<ScreenName>('login-portal');
  const [history, setHistory] = useState<ScreenName[]>(['login-portal']);
  const [selectedLocation, setSelectedLocation] = useState<SelectedLocation>(DEFAULT_LOCATION);
  const [latestAssessmentId, setLatestAssessmentId] = useState<string | null>(null);
  const [incidentDraft, setIncidentDraft] = useState<IncidentReportDraft>(() =>
    createDefaultDraft(DEFAULT_LOCATION)
  );
  const [verificationReports, setVerificationReports] = useState<VerificationReport[]>([]);
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [isRestoringSession, setIsRestoringSession] = useState<boolean>(true);

  const isLoggedInCitizen = currentUser?.role === 'CITIZEN';
  const isLoggedInOfficer =
    currentUser?.role === 'FIELD_OFFICER' ||
    currentUser?.role === 'AUTHORITY' ||
    currentUser?.role === 'ADMIN';

  useEffect(() => {
    let active = true;
    const restore = async () => {
      const token = geoSenseApi.getToken();
      if (!token) {
        if (active) setIsRestoringSession(false);
        return;
      }
      try {
        const user = await geoSenseApi.getMe();
        if (!active) return;
        setCurrentUser(user);
        if (user.role === 'CITIZEN') {
          setRole('citizen');
          setPortalTab('citizen');
          setCurrentScreen('citizen-home');
          setHistory(['citizen-home']);
        } else {
          setRole('officer');
          setPortalTab('officer');
          setCurrentScreen('officer-home');
          setHistory(['officer-home']);
        }
      } catch {
        geoSenseApi.setToken(null);
      } finally {
        if (active) setIsRestoringSession(false);
      }
    };
    restore();
    return () => {
      active = false;
    };
  }, []);

  const determineTab = (screen: ScreenName): TabName => {
    if (role === 'citizen') {
      if (screen === 'citizen-home' || screen === 'safety-outlook') return 'home';
      if (screen === 'map' || screen === 'location-details' || screen === 'understand-risk' || screen === 'evacuation') return 'map';
      if (screen === 'alerts') return 'alerts';
      if (screen === 'profile' || screen === 'offline-maps') return 'profile';
      return 'home';
    } else {
      if (screen === 'officer-home') return 'home';
      if (screen === 'officer-mission' || screen === 'officer-verification' || screen === 'officer-report') return 'missions';
      if (screen === 'officer-alerts') return 'alerts';
      if (screen === 'officer-profile' || screen === 'officer-offline') return 'profile';
      return 'home';
    }
  };

  const activeTab = determineTab(currentScreen);

  const navigate = (screen: ScreenName) => {
    if (screen === 'officer-login' || screen.startsWith('officer-')) {
      setRole('officer');
    } else if (screen !== 'login-portal') {
      setRole('citizen');
    }
    setHistory((prev) => [...prev, screen]);
    setCurrentScreen(screen);
  };

  const goBack = () => {
    if (history.length > 1) {
      const nextHistory = [...history];
      nextHistory.pop();
      const prevScreen = nextHistory[nextHistory.length - 1];
      setHistory(nextHistory);
      setCurrentScreen(prevScreen);
    } else if (isLoggedInOfficer) {
      setCurrentScreen('officer-home');
    } else if (isLoggedInCitizen) {
      setCurrentScreen('citizen-home');
    } else {
      setCurrentScreen('login-portal');
    }
  };

  const updateIncidentDraft = (data: Partial<IncidentReportDraft>) => {
    setIncidentDraft((prev) => ({ ...prev, ...data }));
  };

  const resetIncidentDraft = () => {
    setIncidentDraft(createDefaultDraft(selectedLocation));
  };

  const mapIncidentToVerification = (inc: any): VerificationReport => {
    const rawCat = String(inc.incident_category || 'INCIDENT').replace(/_/g, ' ');
    const titleCaseCat = rawCat.charAt(0).toUpperCase() + rawCat.slice(1).toLowerCase();
    const rawStatus = String(inc.status || 'PENDING').toUpperCase();
    const status: VerificationReport['status'] =
      rawStatus === 'VERIFIED' ? 'verified' : rawStatus === 'REJECTED' ? 'rejected' : 'pending';
    const isHigh =
      inc.incident_category === 'LANDSLIDE' || inc.incident_category === 'FALLING_ROCKS';

    return {
      id: inc.id,
      title: `${titleCaseCat}${inc.location_name ? ` — ${inc.location_name}` : ''}`,
      category: titleCaseCat,
      location: inc.location_name || `${Number(inc.latitude).toFixed(3)}, ${Number(inc.longitude).toFixed(3)}`,
      latitude: Number(inc.latitude),
      longitude: Number(inc.longitude),
      timeAgo: formatRelativeTime(inc.created_at),
      quote: inc.description || 'No description provided.',
      submitter:
        inc.reporter_type === 'officer'
          ? 'Field Officer submission'
          : `Citizen submission${inc.contact_info ? ` • ${inc.contact_info}` : ''}`,
      severity: isHigh ? 'High' : 'Moderate',
      status,
    };
  };

  const refreshOfficerIncidents = async () => {
    if (!geoSenseApi.getToken()) return;
    const res = await geoSenseApi.getOfficerIncidents();
    setVerificationReports((res.incidents || []).map(mapIncidentToVerification));
  };

  const verifyReport = async (id: string, notes?: string) => {
    await geoSenseApi.verifyIncident(id, 'VERIFIED', notes || 'Verified from GeoSense Officer Mobile App');
    setVerificationReports((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: 'verified' } : r))
    );
  };

  const rejectReport = async (id: string, notes?: string) => {
    await geoSenseApi.verifyIncident(id, 'REJECTED', notes || 'Rejected from GeoSense Officer Mobile App');
    setVerificationReports((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: 'rejected' } : r))
    );
  };

  const submitIncidentToBackend = async (): Promise<string> => {
    if (!geoSenseApi.getToken()) {
      throw new Error('Please sign in before submitting an incident report.');
    }
    const categoryMap: Record<string, string> = {
      Landslide: 'LANDSLIDE',
      'Falling Rocks': 'FALLING_ROCKS',
      'Road Blockage': 'ROAD_BLOCKAGE',
      'Slope Cracks': 'SLOPE_CRACKS',
      Flooding: 'FLOODING',
      'Damaged Infrastructure': 'DAMAGED_INFRASTRUCTURE',
    };
    const mappedCategory =
      categoryMap[incidentDraft.type] ||
      incidentDraft.type.toUpperCase().replace(/\s+/g, '_');

    const res = await geoSenseApi.submitIncident({
      incident_category: mappedCategory,
      description:
        incidentDraft.description.trim() ||
        `${incidentDraft.type} reported near ${incidentDraft.location} (Severity: ${incidentDraft.severity}, Road: ${incidentDraft.accessibility})`,
      latitude: incidentDraft.latitude,
      longitude: incidentDraft.longitude,
      location_name: incidentDraft.location,
      state: currentUser?.assigned_state || 'Meghalaya',
      district: currentUser?.assigned_district || 'East Khasi Hills',
      incident_time: incidentDraft.time || new Date().toISOString(),
      contact_info: currentUser?.phone || undefined,
    });
    updateIncidentDraft({ referenceId: res.incident_id });
    return res.incident_id;
  };

  const loginCitizen = async (identifier: string, password: string) => {
    const res = await geoSenseApi.login(identifier, password);
    setCurrentUser(res.user);
    setRole('citizen');
    setPortalTab('citizen');
    setHistory(['citizen-home']);
    setCurrentScreen('citizen-home');
  };

  const registerCitizen = async (
    fullName: string,
    email: string,
    phone: string,
    password: string
  ) => {
    const res = await geoSenseApi.registerCitizen(email, password, fullName, phone);
    setCurrentUser(res.user);
    setRole('citizen');
    setPortalTab('citizen');
    setHistory(['citizen-home']);
    setCurrentScreen('citizen-home');
  };

  const logoutCitizen = () => {
    geoSenseApi.setToken(null);
    setCurrentUser(null);
    setPortalTab('citizen');
    setHistory(['login-portal']);
    setCurrentScreen('login-portal');
  };

  const loginOfficer = async (identifier: string, password: string) => {
    const res = await geoSenseApi.login(identifier, password);
    if (res.user.role === 'CITIZEN') {
      geoSenseApi.setToken(null);
      throw new Error('This account is a Citizen account. Use Field Officer credentials.');
    }
    setCurrentUser(res.user);
    setRole('officer');
    setPortalTab('officer');
    setHistory(['officer-home']);
    setCurrentScreen('officer-home');
  };

  const logoutOfficer = () => {
    geoSenseApi.setToken(null);
    setCurrentUser(null);
    setVerificationReports([]);
    setPortalTab('officer');
    setHistory(['login-portal']);
    setCurrentScreen('login-portal');
  };

  const updateUserProfile = async (fullName: string, phone: string) => {
    const updated = await geoSenseApi.updateMe({ full_name: fullName, phone });
    setCurrentUser(updated);
  };

  return (
    <AppContext.Provider
      value={{
        role,
        setRole,
        portalTab,
        setPortalTab,
        currentScreen,
        activeTab,
        navigate,
        goBack,
        canGoBack: history.length > 1,
        selectedLocation,
        setSelectedLocation,
        latestAssessmentId,
        setLatestAssessmentId,
        incidentDraft,
        updateIncidentDraft,
        resetIncidentDraft,
        submitIncidentToBackend,
        verificationReports,
        refreshOfficerIncidents,
        verifyReport,
        rejectReport,
        currentUser,
        isRestoringSession,
        isLoggedInCitizen,
        isLoggedInOfficer,
        citizenName: currentUser?.full_name || '',
        citizenPhone: currentUser?.phone || '',
        officerId: currentUser?.officer_code || currentUser?.user_id || '',
        loginCitizen,
        registerCitizen,
        logoutCitizen,
        loginOfficer,
        logoutOfficer,
        updateUserProfile,
      }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}
