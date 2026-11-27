import { SafeAreaView } from 'react-native-safe-area-context';
import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { Feather, Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { HeaderBar } from '@/components/HeaderBar';
import { useApp, formatRelativeTime } from '@/context/AppContext';
import { geoSenseApi } from '@/services/api';

export function OfficerHomeScreen() {
  const { navigate, currentUser, officerId } = useApp();
  const [dashboard, setDashboard] = useState<any | null>(null);
  const [alertsCount, setAlertsCount] = useState<number>(0);
  const [lastSynced, setLastSynced] = useState<string>('Syncing...');

  const loadDashboard = async () => {
    try {
      const [dash, alr] = await Promise.all([
        geoSenseApi.getOfficerDashboard(),
        geoSenseApi.getAlerts({ limit: 50 }).catch(() => ({ count: 0, alerts: [] })),
      ]);
      setDashboard(dash);
      setAlertsCount(alr?.count ?? alr?.alerts?.length ?? 0);
      setLastSynced(`Synced at ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`);
    } catch {
      setLastSynced('Offline / unable to sync');
    }
  };

  useEffect(() => {
    if (geoSenseApi.getToken()) {
      loadDashboard();
    }
  }, []);

  const handleSyncData = async () => {
    await loadDashboard();
    Alert.alert('Sync Successful', 'All mission reports, incidents, and alerts are up to date.');
  };

  const todayStr = new Date().toLocaleDateString(undefined, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).toUpperCase();
  const firstName = (currentUser?.full_name || 'Officer').split(' ')[0];
  const district = currentUser?.assigned_district || currentUser?.assigned_state || 'Meghalaya';
  const missions: any[] = [
    ...(dashboard?.inspections || []).slice(0, 2).map((insp: any) => ({
      id: insp.inspection_id,
      title: insp.location_name || insp.location_id,
      sub: `Inspection • ${insp.status}`,
      badge: insp.risk_category_snapshot || 'ACTIVE',
    })),
    ...(dashboard?.incidents || []).filter((i: any) => i.status === 'PENDING').slice(0, 2).map((inc: any) => ({
      id: inc.id,
      title: inc.location_name || inc.incident_category,
      sub: `Incident verification • ${formatRelativeTime(inc.created_at)}`,
      badge: inc.status,
    })),
  ].slice(0, 3);

  return (
    <SafeAreaView style={styles.safeArea} edges={['left', 'right']}>
      <HeaderBar variant="officer-main" />

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}>
        
        {/* Date and On-Duty Badge */}
        <View style={styles.dateRow}>
          <Text style={styles.dateText}>{todayStr}</Text>
          <View style={styles.onDutyBadge}>
            <View style={styles.onDutyDot} />
            <Text style={styles.onDutyText}>On Duty</Text>
          </View>
        </View>

        {/* Greeting & Officer Badge */}
        <View style={styles.greetingBox}>
          <Text style={styles.greetingTitle}>Hello, {firstName}</Text>
          <Text style={styles.officerSubtitle}>
            {officerId} • {district}
          </Text>
        </View>

        {/* Active Alerts Banner */}
        <TouchableOpacity
          style={styles.activeAlertsBanner}
          onPress={() => navigate('officer-alerts')}
          activeOpacity={0.88}>
          <View style={styles.alertLeftCol}>
            <View style={styles.alertIconCircle}>
              <Ionicons name="warning-outline" size={24} color="#FFFFFF" />
            </View>
            <View>
              <Text style={styles.activeAlertsTitle}>{alertsCount} Active Alerts</Text>
              <Text style={styles.activeAlertsSub}>
                {dashboard?.pending_incidents_count ?? 0} pending incidents need verification
              </Text>
            </View>
          </View>
          <Feather name="arrow-up-right" size={24} color="#FFFFFF" />
        </TouchableOpacity>

        {/* Quick Actions Grid */}
        <Text style={styles.sectionTitle}>Quick actions</Text>

        <View style={styles.actionsGrid}>
          {/* 1. New Field Report */}
          <TouchableOpacity
            style={styles.actionCard}
            onPress={() => navigate('officer-report')}
            activeOpacity={0.75}>
            <View style={styles.actionIconBox}>
              <Feather name="camera" size={22} color="#00875A" />
            </View>
            <Text style={styles.actionCardLabel}>New Field{'\n'}Report</Text>
          </TouchableOpacity>

          {/* 2. Assigned Locations */}
          <TouchableOpacity
            style={styles.actionCard}
            onPress={() => navigate('officer-mission')}
            activeOpacity={0.75}>
            <View style={styles.actionIconBox}>
              <Feather name="map-pin" size={22} color="#00875A" />
            </View>
            <Text style={styles.actionCardLabel}>Assigned{'\n'}Locations</Text>
          </TouchableOpacity>

          {/* 3. Incident Verification */}
          <TouchableOpacity
            style={styles.actionCard}
            onPress={() => navigate('officer-verification')}
            activeOpacity={0.75}>
            <View style={styles.actionIconBox}>
              <Feather name="shield" size={22} color="#00875A" />
            </View>
            <Text style={styles.actionCardLabel}>Incident{'\n'}Verification</Text>
          </TouchableOpacity>

          {/* 4. Priority Alerts */}
          <TouchableOpacity
            style={styles.actionCard}
            onPress={() => navigate('officer-alerts')}
            activeOpacity={0.75}>
            <View style={styles.actionIconBox}>
              <Feather name="bell" size={22} color="#00875A" />
            </View>
            <Text style={styles.actionCardLabel}>Priority{'\n'}Alerts</Text>
          </TouchableOpacity>

          {/* 5. Offline Maps */}
          <TouchableOpacity
            style={styles.actionCard}
            onPress={() => navigate('officer-offline')}
            activeOpacity={0.75}>
            <View style={styles.actionIconBox}>
              <Feather name="download" size={22} color="#00875A" />
            </View>
            <Text style={styles.actionCardLabel}>Offline{'\n'}Maps</Text>
          </TouchableOpacity>

          {/* 6. Sync Data */}
          <TouchableOpacity
            style={styles.actionCard}
            onPress={handleSyncData}
            activeOpacity={0.75}>
            <View style={styles.actionIconBox}>
              <Feather name="rotate-cw" size={22} color="#00875A" />
            </View>
            <Text style={styles.actionCardLabel}>Sync{'\n'}Data</Text>
          </TouchableOpacity>
        </View>

        {/* Today's Missions */}
        <View style={styles.missionsHeaderRow}>
          <Text style={styles.sectionTitle}>Today’s Missions</Text>
          <TouchableOpacity onPress={() => navigate('officer-mission')} activeOpacity={0.7}>
            <Text style={styles.viewAllText}>View all ({missions.length})</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.missionsCard}>
          {missions.length === 0 ? (
            <Text style={{ padding: 16, color: '#64748B', fontSize: 13 }}>
              No active missions or pending incidents.
            </Text>
          ) : (
            missions.map((m, idx) => (
              <React.Fragment key={m.id}>
                {idx > 0 && <View style={styles.missionDivider} />}
                <TouchableOpacity
                  style={styles.missionItem}
                  onPress={() => navigate('officer-mission')}
                  activeOpacity={0.7}>
                  <View style={styles.missionPinBox}>
                    <Feather name="map-pin" size={18} color="#00875A" />
                  </View>
                  <View style={styles.missionInfo}>
                    <Text style={styles.missionTitle}>{m.title}</Text>
                    <Text style={styles.missionSub}>{m.sub}</Text>
                  </View>
                  <View style={m.badge === 'CRITICAL' || m.badge === 'HIGH' ? styles.highPriorityBadge : styles.pendingBadge}>
                    <Text style={m.badge === 'CRITICAL' || m.badge === 'HIGH' ? styles.highPriorityText : styles.pendingText}>
                      {m.badge}
                    </Text>
                  </View>
                </TouchableOpacity>
              </React.Fragment>
            ))
          )}
        </View>

        {/* Sync Status Footer */}
        <View style={styles.syncFooterRow}>
          <Feather name="cloud" size={14} color="#00875A" />
          <Text style={styles.syncFooterText}>{lastSynced}</Text>
        </View>

      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#0D5C3A',
  },
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  contentContainer: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 95,
  },
  dateRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  dateText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#64748B',
    letterSpacing: 0.8,
  },
  onDutyBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#D1FAE5',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 12,
    gap: 5,
  },
  onDutyDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#10B981',
  },
  onDutyText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#065F46',
  },
  greetingBox: {
    marginBottom: 18,
  },
  greetingTitle: {
    fontSize: 26,
    fontWeight: '800',
    color: '#0F172A',
    letterSpacing: -0.5,
  },
  officerSubtitle: {
    fontSize: 13,
    color: '#64748B',
    marginTop: 4,
  },
  activeAlertsBanner: {
    backgroundColor: '#EA3838',
    borderRadius: 22,
    padding: 18,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    shadowColor: '#EA3838',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 10,
    elevation: 4,
    marginBottom: 24,
  },
  alertLeftCol: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
  },
  alertIconCircle: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  activeAlertsTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  activeAlertsSub: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.85)',
    marginTop: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 14,
  },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    rowGap: 14,
    marginBottom: 24,
  },
  actionCard: {
    width: '31%',
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    paddingVertical: 16,
    paddingHorizontal: 6,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 2,
    borderWidth: 1,
    borderColor: '#F1F5F9',
  },
  actionIconBox: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: '#E8F5E9',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  actionCardLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: '#334155',
    textAlign: 'center',
    lineHeight: 15,
  },
  missionsHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  viewAllText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#00875A',
  },
  missionsCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 20,
  },
  missionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 8,
  },
  missionPinBox: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#E8F5E9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  missionInfo: {
    flex: 1,
  },
  missionTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
  },
  missionSub: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
  highPriorityBadge: {
    backgroundColor: '#FEE2E2',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
  },
  highPriorityText: {
    color: '#DC2626',
    fontSize: 11,
    fontWeight: '700',
  },
  pendingBadge: {
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
  },
  pendingText: {
    color: '#B45309',
    fontSize: 11,
    fontWeight: '700',
  },
  missionDivider: {
    height: 1,
    backgroundColor: '#F1F5F9',
    marginVertical: 8,
  },
  syncFooterRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  syncFooterText: {
    fontSize: 12,
    color: '#64748B',
    fontWeight: '500',
  },
});

