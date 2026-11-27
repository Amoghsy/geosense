import { SafeAreaView } from 'react-native-safe-area-context';
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { Feather, Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { HeaderBar } from '@/components/HeaderBar';
import { useApp } from '@/context/AppContext';
import { geoSenseApi } from '@/services/api';

export function OfficerAlertsScreen() {
  const { navigate } = useApp();
  const [activeFilter, setActiveFilter] = useState('All');
  const [liveOfficerAlerts, setLiveOfficerAlerts] = useState<any[] | null>(null);

  useEffect(() => {
    if (!geoSenseApi.getToken()) return;
    geoSenseApi.getNotifications()
      .then((res) => {
        if (res?.notifications?.length) setLiveOfficerAlerts(res.notifications);
      })
      .catch(() => {});
  }, []);

  const filters = [
    { label: 'All 3', key: 'All' },
    { label: 'Critical 1', key: 'Critical' },
    { label: 'High 1', key: 'High' },
    { label: 'Moderate 1', key: 'Moderate' },
  ];

  const alerts = [
    {
      id: '1',
      severity: 'Critical',
      time: '09:35 AM',
      icon: <Ionicons name="warning-outline" size={18} color="#DC2626" />,
      title: 'Landslide warning',
      corridor: 'Sohra slope · SH-5 corridor',
      desc: 'Rapid soil movement detected after prolonged rainfall. Avoid the slope and verify on site.',
      source: 'GeoSense AI • 96% confidence',
      accentColor: '#DC2626',
      badgeBg: '#FEE2E2',
      badgeText: '#DC2626',
      target: 'officer-mission' as const,
    },
    {
      id: '2',
      severity: 'High',
      time: '09:18 AM',
      icon: <Feather name="cloud-rain" size={18} color="#D97706" />,
      title: 'Heavy rainfall alert',
      corridor: 'Mawsynram & adjoining areas',
      desc: '82 mm recorded in 3 hours. Further intense rainfall likely. Monitor vulnerable slopes.',
      source: 'IMD • District control room',
      accentColor: '#D97706',
      badgeBg: '#FEF3C7',
      badgeText: '#B45309',
      target: 'officer-mission' as const,
    },
    {
      id: '3',
      severity: 'Moderate',
      time: '08:54 AM',
      icon: <MaterialCommunityIcons name="cone" size={18} color="#EA580C" />,
      title: 'Road partially blocked',
      corridor: 'Pynursla road · NH-206',
      desc: 'Debris cleared from one lane. Proceed with caution; traffic is moving slowly.',
      source: 'PWD • Road status update',
      accentColor: '#EA580C',
      badgeBg: '#FFEDD5',
      badgeText: '#C2410C',
      target: 'officer-verification' as const,
    },
  ];

  const filteredAlerts = alerts.filter(
    (a) => activeFilter === 'All' || a.severity === activeFilter
  );

  return (
    <SafeAreaView style={styles.safeArea} edges={['left', 'right']}>
      <HeaderBar
        title="Alerts"
        subtitle="EAST KHASI HILLS"
        variant="officer-dark"
        rightAction={
          <TouchableOpacity hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
            <Feather name="sliders" size={20} color="#FFFFFF" />
          </TouchableOpacity>
        }
      />

      {/* Filter Tabs */}
      <View style={styles.filtersWrapper}>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.filtersScroll}>
          {filters.map((f) => {
            const isSelected = activeFilter === f.key;
            return (
              <TouchableOpacity
                key={f.key}
                style={[styles.filterPill, isSelected && styles.filterPillActive]}
                onPress={() => setActiveFilter(f.key)}>
                <Text
                  style={[styles.filterPillText, isSelected && styles.filterPillTextActive]}>
                  {f.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </View>

      {/* Subheader */}
      <View style={styles.subHeaderRow}>
        <Text style={styles.subHeaderTitle}>Today’s updates</Text>
        <TouchableOpacity>
          <Text style={styles.markReadText}>Mark all read</Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}>
        {filteredAlerts.map((item) => (
          <TouchableOpacity
            key={item.id}
            style={[styles.alertCard, { borderLeftColor: item.accentColor }]}
            onPress={() => navigate(item.target)}
            activeOpacity={0.8}>
            <View style={styles.cardTopRow}>
              <View style={[styles.severityBadge, { backgroundColor: item.badgeBg }]}>
                <View style={[styles.badgeDot, { backgroundColor: item.badgeText }]} />
                <Text style={[styles.badgeText, { color: item.badgeText }]}>
                  {item.severity}
                </Text>
              </View>
              <Text style={styles.alertTime}>{item.time}</Text>
            </View>

            <View style={styles.titleRow}>
              <View style={styles.titleWithIcon}>
                {item.icon}
                <Text style={styles.alertTitle}>{item.title}</Text>
              </View>
              <Feather name="chevron-right" size={18} color="#94A3B8" />
            </View>

            <Text style={styles.corridorText}>{item.corridor}</Text>
            <Text style={styles.descText}>{item.desc}</Text>

            <Text style={styles.sourceText}>{item.source}</Text>
          </TouchableOpacity>
        ))}

        {/* Live Monitoring Indicator */}
        <View style={styles.liveMonitoringRow}>
          <View style={styles.pulseGreenDot} />
          <Text style={styles.liveMonitoringText}>
            Live monitoring • Updated just now
          </Text>
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
  filtersWrapper: {
    backgroundColor: '#0D5C3A',
    paddingVertical: 12,
  },
  filtersScroll: {
    paddingHorizontal: 20,
    gap: 10,
  },
  filterPill: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.15)',
  },
  filterPillActive: {
    backgroundColor: '#FFFFFF',
  },
  filterPillText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#E2E8F0',
  },
  filterPillTextActive: {
    color: '#0D5C3A',
  },
  subHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 14,
    backgroundColor: '#F8FAFC',
  },
  subHeaderTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#0F172A',
  },
  markReadText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#00875A',
  },
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  contentContainer: {
    paddingHorizontal: 20,
    paddingBottom: 95,
    gap: 14,
  },
  alertCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 18,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderLeftWidth: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
    elevation: 2,
  },
  cardTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  severityBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 12,
    gap: 5,
  },
  badgeDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: '800',
  },
  alertTime: {
    fontSize: 12,
    color: '#64748B',
    fontWeight: '600',
  },
  titleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  titleWithIcon: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  alertTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#0F172A',
  },
  corridorText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#475569',
    marginBottom: 8,
  },
  descText: {
    fontSize: 13,
    color: '#334155',
    lineHeight: 19,
    marginBottom: 12,
  },
  sourceText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#00875A',
  },
  liveMonitoringRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 8,
  },
  pulseGreenDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#10B981',
  },
  liveMonitoringText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#64748B',
  },
});

