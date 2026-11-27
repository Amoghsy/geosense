import React, { createContext, useContext, useState, ReactNode } from 'react';

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

export interface IncidentReportDraft {
  type: string;
  location: string;
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
  location: string;
  distance: string;
  timeAgo: string;
  quote: string;
  submitter: string;
  severity: 'High' | 'Moderate';
  photosCount: number;
  status: 'pending' | 'verified' | 'rejected';
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
  incidentDraft: IncidentReportDraft;
  updateIncidentDraft: (data: Partial<IncidentReportDraft>) => void;
  resetIncidentDraft: () => void;
  verificationReports: VerificationReport[];
  verifyReport: (id: string) => void;
  rejectReport: (id: string) => void;
  isLoggedInCitizen: boolean;
  isLoggedInOfficer: boolean;
  citizenName: string;
  citizenPhone: string;
  officerId: string;
  loginCitizen: (name?: string, phone?: string) => void;
  logoutCitizen: () => void;
  loginOfficer: (id?: string) => void;
  logoutOfficer: () => void;
}

const defaultIncidentDraft: IncidentReportDraft = {
  type: 'Landslide',
  location: 'Cherrapunji',
  coords: '25.2702° N, 91.7323° E',
  accuracy: '±4 m',
  description: 'Fresh slope failure after heavy rainfall. Rocks and debris partially block the road. Soil remains unstable.',
  severity: 'High',
  accessibility: 'Partially blocked',
  peopleAffected: 'Not known',
  referenceId: 'GS-2026-01482',
};

const initialVerificationReports: VerificationReport[] = [
  {
    id: 'INC-2026-0842',
    title: 'Rockfall near Sohra viewpoint',
    location: 'Sohra, SH-5',
    distance: '2.8 km away',
    timeAgo: '12 min ago',
    quote: 'Large rocks have fallen onto the road. Only one lane is open. More debris is coming down.',
    submitter: 'B. Khongwir • Citizen submission',
    severity: 'High',
    photosCount: 3,
    status: 'pending',
  },
  {
    id: 'INC-2026-0841',
    title: 'Cracks along roadside',
    location: 'Mawsynram',
    distance: '6.4 km away',
    timeAgo: '28 min ago',
    quote: 'Significant surface cracks observed stretching 15 meters along the mountain shoulder.',
    submitter: 'L. Marak • Citizen submission',
    severity: 'Moderate',
    photosCount: 2,
    status: 'pending',
  },
];

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [role, setRole] = useState<UserRole>('citizen');
  const [portalTab, setPortalTab] = useState<'citizen' | 'officer'>('citizen');
  const [currentScreen, setCurrentScreen] = useState<ScreenName>('login-portal');
  const [history, setHistory] = useState<ScreenName[]>(['login-portal']);
  const [incidentDraft, setIncidentDraft] = useState<IncidentReportDraft>(defaultIncidentDraft);
  const [verificationReports, setVerificationReports] = useState<VerificationReport[]>(initialVerificationReports);
  const [isLoggedInCitizen, setIsLoggedInCitizen] = useState<boolean>(false);
  const [isLoggedInOfficer, setIsLoggedInOfficer] = useState<boolean>(false);
  const [citizenName, setCitizenName] = useState<string>('Aiban Khonglah');
  const [citizenPhone, setCitizenPhone] = useState<string>('+91 98630 01482');
  const [officerId, setOfficerId] = useState<string>('FO-1027');

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
    // Determine role context
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
    } else {
      // Default fallback
      if (isLoggedInOfficer) {
        setCurrentScreen('officer-home');
      } else if (isLoggedInCitizen) {
        setCurrentScreen('citizen-home');
      } else {
        setCurrentScreen('login-portal');
      }
    }
  };

  const updateIncidentDraft = (data: Partial<IncidentReportDraft>) => {
    setIncidentDraft((prev) => ({ ...prev, ...data }));
  };

  const resetIncidentDraft = () => {
    setIncidentDraft(defaultIncidentDraft);
  };

  const verifyReport = (id: string) => {
    setVerificationReports((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: 'verified' } : r))
    );
  };

  const rejectReport = (id: string) => {
    setVerificationReports((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: 'rejected' } : r))
    );
  };

  const loginCitizen = (name?: string, phone?: string) => {
    if (name && name.trim()) setCitizenName(name.trim());
    if (phone && phone.trim()) setCitizenPhone(phone.trim());
    setIsLoggedInCitizen(true);
    setRole('citizen');
    navigate('citizen-home');
  };

  const logoutCitizen = () => {
    setIsLoggedInCitizen(false);
    setPortalTab('citizen');
    navigate('login-portal');
  };

  const loginOfficer = (id?: string) => {
    if (id && id.trim()) setOfficerId(id.trim());
    setIsLoggedInOfficer(true);
    setRole('officer');
    navigate('officer-home');
  };

  const logoutOfficer = () => {
    setIsLoggedInOfficer(false);
    setPortalTab('officer');
    navigate('login-portal');
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
        incidentDraft,
        updateIncidentDraft,
        resetIncidentDraft,
        verificationReports,
        verifyReport,
        rejectReport,
        isLoggedInCitizen,
        isLoggedInOfficer,
        citizenName,
        citizenPhone,
        officerId,
        loginCitizen,
        logoutCitizen,
        loginOfficer,
        logoutOfficer,
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
