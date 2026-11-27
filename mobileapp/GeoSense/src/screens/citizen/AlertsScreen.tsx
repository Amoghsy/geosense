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
import { useApp, formatRelativeTime } from '@/context/AppContext';
import { geoSenseApi } from '@/services/api';

interface DisplayAlert {
  id: string;
  notificationId?: string;
  category: string;
  title: string;
  titleColor: string;
  location: string;
  time: string;
  desc: string;
  icon: React.ReactNode;
  iconBg: string;
  isUnread: boolean;
  targetScreen: 'location-details' | 'safety-outlook' | 'evacuation';
}

export function AlertsScreen() {
  const { navigate } = useApp();
  const [selectedFilter, setSelectedFilter] = useState('All');
  const [alerts, setAlerts] = useState<DisplayAlert[]>([]);
  const [loading, setLoading] = useState(true);

  const mapBackendItem = (item: any, isNotification: boolean): DisplayAlert => {
    const severity = String(item.severity || 'WARNING').toUpperCase();
    const title = String(item.title || 'GeoSense Alert');
    const titleUpper = title.toUpperCase();

    let category = 'Advisory';
    let targetScreen: DisplayAlert['targetScreen'] = 'evacuation';
    let iconBg = '#D1FAE5';
    let titleColor = '#059669';
    let icon: React.ReactNode = <MaterialCommunityIcons name="call-split" size={22} color="#059669" />;

    if (severity === 'CRITICAL' || titleUpper.includes('LANDSLIDE')) {
      category = 'High Risk';
      targetScreen = 'location-details';
      iconBg = '#FEE2E2';
      titleColor = '#EF4444';
      icon = <Ionicons name="warning-outline" size={22} color="#EF4444" />;
    } else if (titleUpper.includes('RAIN') || titleUpper.includes('WEATHER')) {
      category = 'Weather';
      targetScreen = 'safety-outlook';
      iconBg = '#FEF3C7';
      titleColor = '#D97706';
      icon = <Feather name="cloud-rain" size={22} color="#D97706" />;
    } else if (titleUpper.includes('ROAD') || titleUpper.includes('BLOCK')) {
      category = 'Road Updates';
      targetScreen = 'evacuation';
      iconBg = '#FFEDD5';
      titleColor = '#EA580C';
      icon = <MaterialCommunityIcons name="road-variant" size={22} color="#EA580C" />;
    }

    return {
      id: item.alert_id || item.notification_id,
      notificationId: isNotification ? item.notification_id : undefined,
      category,
      title,
      titleColor,
      location: item.location_name || item.state || 'Meghalaya',
      time: formatRelativeTime(item.published_at || item.created_at),
      desc: item.message || item.description || '',
      icon,
      iconBg,
      isUnread: isNotification ? !item.is_read : false,
      targetScreen,
    };
  };

  useEffect(() => {
    let active = true;
    const loadAlerts = async () => {
      if (!geoSenseApi.getToken()) {
        if (active) setLoading(false);
        return;
      }
      try {
        const [notifRes, alertRes] = await Promise.all([
          geoSenseApi.getNotifications().catch(() => ({ notifications: [] })),
          geoSenseApi.getAlerts().catch(() => ({ alerts: [] })),
        ]);
        if (!active) return;
        const notifs = (notifRes?.notifications || []).map((n: any) => mapBackendItem(n, true));
        if (notifs.length > 0) {
          setAlerts(notifs);
        } else {
          setAlerts((alertRes?.alerts || []).map((a: any) => mapBackendItem(a, false)));
        }
      } finally {
        if (active) setLoading(false);
      }
    };
    loadAlerts();
    return () => {
      active = false;
    };
  }, []);

  const unreadCount = alerts.filter((a) => a.isUnread).length;

  const handleMarkAllRead = async () => {
    const unread = alerts.filter((a) => a.isUnread && a.notificationId);
    setAlerts((prev) => prev.map((a) => ({ ...a, isUnread: false })));
    await Promise.all(
      unread.map((u) => geoSenseApi.markNotificationRead(u.notificationId!).catch(() => null))
    );
  };

  const filters = ['All', 'High Risk', 'Weather', 'Road Updates', 'Advisory'];

  const filteredAlerts = alerts.filter(
    (a) => selectedFilter === 'All' || a.category === selectedFilter
  );

  return (
    <SafeAreaView style={styles.safeArea} edges={['left', 'right']}>
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
        <TouchableOpacity onPress={handleMarkAllRead}>
          <Text style={styles.markReadText}>Mark all as read</Text>
        </TouchableOpacity>
      </View>

      {/* Alerts Cards List */}
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}>
        {loading && (
          <Text style={{ textAlign: 'center', color: '#64748B', paddingVertical: 24 }}>
            Loading alerts from GeoSense server...
          </Text>
        )}
        {!loading && filteredAlerts.length === 0 && (
          <Text style={{ textAlign: 'center', color: '#64748B', paddingVertical: 24 }}>
            No published alerts in this category.
          </Text>
        )}
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
    paddingBottom: 95,
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

