import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
} from 'react-native';
import { Feather, Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { HeaderBar } from '@/components/HeaderBar';
import { useApp } from '@/context/AppContext';

export function AlertsScreen() {
  const { navigate } = useApp();
  const [selectedFilter, setSelectedFilter] = useState('All');
  const [unreadCount, setUnreadCount] = useState(2);

  const filters = ['All', 'High Risk', 'Weather', 'Road Updates', 'Advisory'];

  const alerts = [
    {
      id: '1',
      category: 'High Risk',
      title: 'HIGH LANDSLIDE RISK',
      titleColor: '#EF4444',
      location: 'Cherrapunji',
      time: '5 min ago',
      desc: '87% landslide probability · Next 6 Hours. Avoid unstable slopes and mountain roads.',
      icon: <Ionicons name="warning-outline" size={22} color="#EF4444" />,
      iconBg: '#FEE2E2',
      isUnread: true,
      targetScreen: 'location-details' as const,
    },
    {
      id: '2',
      category: 'Weather',
      title: 'HEAVY RAINFALL WARNING',
      titleColor: '#D97706',
      location: 'Meghalaya East',
      time: '18 min ago',
      desc: 'Heavy rainfall expected over the Next 24 Hours. Stay alert for rapid changes.',
      icon: <Feather name="cloud-rain" size={22} color="#D97706" />,
      iconBg: '#FEF3C7',
      isUnread: true,
      targetScreen: 'safety-outlook' as const,
    },
    {
      id: '3',
      category: 'Road Updates',
      title: 'ROAD BLOCKAGE UPDATE',
      titleColor: '#EA580C',
      location: 'NH-206',
      time: '42 min ago',
      desc: 'Partial blockage reported near Sohra. Use alternate routes and travel with care.',
      icon: <MaterialCommunityIcons name="road-variant" size={22} color="#EA580C" />,
      iconBg: '#FFEDD5',
      isUnread: false,
      targetScreen: 'evacuation' as const,
    },
    {
      id: '4',
      category: 'Advisory',
      title: 'EVACUATION ADVISORY',
      titleColor: '#059669',
      location: 'High-risk villages',
      time: '1 hour ago',
      desc: 'Keep essentials ready. Follow local authority instructions and designated safe routes.',
      icon: <MaterialCommunityIcons name="call-split" size={22} color="#059669" />,
      iconBg: '#D1FAE5',
      isUnread: false,
      targetScreen: 'evacuation' as const,
    },
  ];

  const filteredAlerts = alerts.filter(
    (a) => selectedFilter === 'All' || a.category === selectedFilter
  );

  return (
    <SafeAreaView style={styles.safeArea}>
      <HeaderBar title="Alerts & Notifications" variant="sub-light" />

      {/* Filter Chips */}
      <View style={styles.filtersWrapper}>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.filtersScroll}>
          {filters.map((f) => {
            const isSelected = selectedFilter === f;
            return (
              <TouchableOpacity
                key={f}
                style={[styles.filterChip, isSelected && styles.filterChipActive]}
                onPress={() => setSelectedFilter(f)}>
                <Text
                  style={[styles.filterChipText, isSelected && styles.filterChipTextActive]}>
                  {f}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </View>

      {/* Subheader: Today unread count & Mark all as read */}
      <View style={styles.subHeaderRow}>
        <Text style={styles.todayCountText}>Today · {unreadCount} unread</Text>
        <TouchableOpacity onPress={() => setUnreadCount(0)}>
          <Text style={styles.markReadText}>Mark all as read</Text>
        </TouchableOpacity>
      </View>

      {/* Alerts Cards List */}
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}>
        {filteredAlerts.map((alert) => (
          <View key={alert.id} style={styles.alertCard}>
            <View style={styles.cardTopRow}>
              <View style={[styles.iconBox, { backgroundColor: alert.iconBg }]}>
                {alert.icon}
              </View>

              <View style={styles.cardHeaderInfo}>
                <View style={styles.titleRow}>
                  <Text style={[styles.alertTitle, { color: alert.titleColor }]}>
                    {alert.title}
                  </Text>
                  {alert.isUnread && unreadCount > 0 && <View style={styles.unreadDot} />}
                </View>
                <View style={styles.metaRow}>
                  <Text style={styles.locationMeta}>{alert.location}</Text>
                  <Text style={styles.timeMeta}>{alert.time}</Text>
                </View>
              </View>
            </View>

            <Text style={styles.alertDesc}>{alert.desc}</Text>

            <TouchableOpacity
              style={styles.viewDetailsRow}
              onPress={() => navigate(alert.targetScreen)}
              activeOpacity={0.7}>
              <Text style={styles.viewDetailsText}>View Details</Text>
              <Feather name="arrow-right" size={14} color="#00875A" />
            </TouchableOpacity>
          </View>
        ))}

        <Text style={styles.footerNotice}>
          Follow official advisories. Call 112 for urgent assistance.
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  filtersWrapper: {
    paddingVertical: 10,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  filtersScroll: {
    paddingHorizontal: 20,
    gap: 8,
  },
  filterChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#F1F5F9',
  },
  filterChipActive: {
    backgroundColor: '#0F172A',
  },
  filterChipText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#64748B',
  },
  filterChipTextActive: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  subHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 14,
    backgroundColor: '#F8FAFC',
  },
  todayCountText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
  },
  markReadText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#00875A',
  },
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  contentContainer: {
    paddingHorizontal: 20,
    paddingBottom: 40,
    gap: 14,
  },
  alertCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 18,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
    elevation: 2,
  },
  cardTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    marginBottom: 10,
  },
  iconBox: {
    width: 44,
    height: 44,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardHeaderInfo: {
    flex: 1,
  },
  titleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  alertTitle: {
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 0.6,
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#EF4444',
  },
  metaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 2,
  },
  locationMeta: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
  },
  timeMeta: {
    fontSize: 12,
    color: '#64748B',
  },
  alertDesc: {
    fontSize: 13,
    color: '#334155',
    lineHeight: 19,
    marginBottom: 14,
  },
  viewDetailsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  viewDetailsText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#00875A',
  },
  footerNotice: {
    textAlign: 'center',
    fontSize: 12,
    color: '#94A3B8',
    marginTop: 10,
  },
});

