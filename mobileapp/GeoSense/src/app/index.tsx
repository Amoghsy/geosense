import React from 'react';
import { View, StyleSheet } from 'react-native';
import { useApp } from '@/context/AppContext';
import { BottomNavBar } from '@/components/BottomNavBar';

// Authentication & Portal Screens
import { LoginPortalScreen } from '@/screens/auth/LoginPortalScreen';

// Citizen Screens
import { CitizenHomeScreen } from '@/screens/citizen/CitizenHomeScreen';
import { SafetyOutlookScreen } from '@/screens/citizen/SafetyOutlookScreen';
import { LiveRiskMapScreen } from '@/screens/citizen/LiveRiskMapScreen';
import { LocationRiskDetailsScreen } from '@/screens/citizen/LocationRiskDetailsScreen';
import { UnderstandRiskScreen } from '@/screens/citizen/UnderstandRiskScreen';
import { EvacuationGuidanceScreen } from '@/screens/citizen/EvacuationGuidanceScreen';
import { NearbyResourcesScreen } from '@/screens/citizen/NearbyResourcesScreen';
import { ReportIncidentStep1Screen } from '@/screens/citizen/ReportIncidentStep1Screen';
import { ReportIncidentStep2Screen } from '@/screens/citizen/ReportIncidentStep2Screen';
import { ReportIncidentSuccessScreen } from '@/screens/citizen/ReportIncidentSuccessScreen';
import { AlertsScreen } from '@/screens/citizen/AlertsScreen';
import { CitizenProfileScreen } from '@/screens/citizen/CitizenProfileScreen';
import { OfflineMapsScreen } from '@/screens/citizen/OfflineMapsScreen';

// Field Officer Screens
import { OfficerLoginScreen } from '@/screens/officer/OfficerLoginScreen';
import { OfficerHomeScreen } from '@/screens/officer/OfficerHomeScreen';
import { OfficerMissionScreen } from '@/screens/officer/OfficerMissionScreen';
import { OfficerIncidentVerificationScreen } from '@/screens/officer/OfficerIncidentVerificationScreen';
import { OfficerNewReportScreen } from '@/screens/officer/OfficerNewReportScreen';
import { OfficerAlertsScreen } from '@/screens/officer/OfficerAlertsScreen';
import { OfficerOfflineScreen } from '@/screens/officer/OfficerOfflineScreen';
import { OfficerProfileScreen } from '@/screens/officer/OfficerProfileScreen';

export default function AppMain() {
  const { currentScreen } = useApp();

  const renderScreen = () => {
    switch (currentScreen) {
      // Auth / Portal screen
      case 'login-portal':
        return <LoginPortalScreen />;

      // Citizen screens
      case 'citizen-home':
        return <CitizenHomeScreen />;
      case 'safety-outlook':
        return <SafetyOutlookScreen />;
      case 'map':
        return <LiveRiskMapScreen />;
      case 'location-details':
        return <LocationRiskDetailsScreen />;
      case 'understand-risk':
        return <UnderstandRiskScreen />;
      case 'evacuation':
        return <EvacuationGuidanceScreen />;
      case 'resources':
        return <NearbyResourcesScreen />;
      case 'report-incident-1':
        return <ReportIncidentStep1Screen />;
      case 'report-incident-2':
        return <ReportIncidentStep2Screen />;
      case 'report-incident-success':
        return <ReportIncidentSuccessScreen />;
      case 'alerts':
        return <AlertsScreen />;
      case 'profile':
        return <CitizenProfileScreen />;
      case 'offline-maps':
        return <OfflineMapsScreen />;

      // Field Officer screens
      case 'officer-login':
        return <OfficerLoginScreen />;
      case 'officer-home':
        return <OfficerHomeScreen />;
      case 'officer-mission':
        return <OfficerMissionScreen />;
      case 'officer-verification':
        return <OfficerIncidentVerificationScreen />;
      case 'officer-report':
        return <OfficerNewReportScreen />;
      case 'officer-alerts':
        return <OfficerAlertsScreen />;
      case 'officer-offline':
        return <OfficerOfflineScreen />;
      case 'officer-profile':
        return <OfficerProfileScreen />;

      default:
        return <LoginPortalScreen />;
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.screenContainer}>{renderScreen()}</View>
      <BottomNavBar />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  screenContainer: {
    flex: 1,
  },
});
