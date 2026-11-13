import React, { createContext, useContext, useState, ReactNode } from 'react';

export type UserRole = 'citizen' | 'officer';

export type ScreenName =
  // Citizen screens
  | 'citizen-home'
  | 'safety-outlook'
  | 'map'
  | 'location-details'
  | 'understand-risk'
  | 'evacuation'
  | 'ar-view'
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
  | 'officer-ar'
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
  isLoggedInOfficer: boolean;
  loginOfficer: () => void;
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
  const [currentScreen, setCurrentScreen] = useState<ScreenName>('citizen-home');
  const [history, setHistory] = useState<ScreenName[]>(['citizen-home']);
  const [incidentDraft, setIncidentDraft] = useState<IncidentReportDraft>(defaultIncidentDraft);
  const [verificationReports, setVerificationReports] = useState<VerificationReport[]>(initialVerificationReports);
  const [isLoggedInOfficer, setIsLoggedInOfficer] = useState<boolean>(false);

  const determineTab = (screen: ScreenName): TabName => {
    if (role === 'citizen') {
      if (screen === 'citizen-home' || screen === 'safety-outlook') return 'home';
      if (screen === 'map' || screen === 'location-details' || screen === 'understand-risk' || screen === 'evacuation' || screen === 'ar-view') return 'map';
      if (screen === 'alerts') return 'alerts';
      if (screen === 'profile' || screen === 'offline-maps') return 'profile';
      return 'home';
    } else {
      if (screen === 'officer-home') return 'home';
      if (screen === 'officer-mission' || screen === 'officer-verification' || screen === 'officer-report' || screen === 'officer-ar') return 'missions';
      if (screen === 'officer-alerts') return 'alerts';
      if (screen === 'officer-profile' || screen === 'officer-offline') return 'profile';
      return 'home';
    }
  };

  const activeTab = determineTab(currentScreen);

  const navigate = (screen: ScreenName) => {
    // Determine if switching role context
    if (screen.startsWith('officer-') && screen !== 'officer-login') {
      setRole('officer');
    } else if (!screen.startsWith('officer-')) {
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
      if (role === 'citizen') {
        setCurrentScreen('citizen-home');
      } else {
        setCurrentScreen('officer-home');
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

  const loginOfficer = () => {
    setIsLoggedInOfficer(true);
    setRole('officer');
    navigate('officer-home');
  };

  const logoutOfficer = () => {
    setIsLoggedInOfficer(false);
    setRole('citizen');
    navigate('citizen-home');
  };

  return (
    <AppContext.Provider
      value={{
        role,
        setRole,
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
        isLoggedInOfficer,
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

