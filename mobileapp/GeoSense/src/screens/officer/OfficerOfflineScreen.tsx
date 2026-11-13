import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  Alert,
} from 'react-native';
import { Feather, Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { HeaderBar } from '@/components/HeaderBar';

export function OfficerOfflineScreen() {
  const [lastSync, setLastSync] = useState('Today, 09:32 AM');
  const [syncing, setSyncing] = useState(false);

  const handleSyncNow = () => {
    setSyncing(true);
    setTimeout(() => {
      setSyncing(false);
      setLastSync('Today, Just now');
      Alert.alert('Synchronized', 'All pending reports uploaded and maps synchronized.');
    }, 1200);
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <HeaderBar
        title="Offline Mode"
        variant="officer-dark"
        rightAction={
          <TouchableOpacity hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
            <Feather name="wifi-off" size={20} color="#FFFFFF" />
          </TouchableOpacity>
        }
      />

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}>
        
        {/* Amber Offline Alert Banner */}
        <View style={styles.offlineAlertCard}>
          <View style={styles.offlineIconBox}>
            <Feather name="wifi-off" size={24} color="#D97706" />
          </View>
          <View style={styles.offlineTextCol}>
            <Text style={styles.offlineTitle}>Working offline</Text>
            <Text style={styles.offlineSubTitle}>No network connection detected</Text>
            <Text style={styles.offlineDesc}>
              Keep working in the field. Your reports are saved on this device until you reconnect.
            </Text>
          </View>
        </View>

        {/* Available Offline Items */}
        <Text style={styles.sectionTitle}>Available offline</Text>

        <View style={styles.availableList}>
          {/* Item 1: Downloaded maps */}
          <View style={styles.availableItem}>
            <View style={styles.itemIconBox}>
              <Feather name="map" size={20} color="#00875A" />
            </View>
            <View style={styles.itemInfo}>
              <Text style={styles.itemTitle}>Downloaded maps</Text>
              <Text style={styles.itemSub}>East Khasi Hills • 234 MB</Text>
            </View>
            <View style={styles.readyBadge}>
              <Text style={styles.readyBadgeText}>Ready</Text>
            </View>
          </View>

          <View style={styles.itemDivider} />

          {/* Item 2: Cached locations */}
          <View style={styles.availableItem}>
            <View style={styles.itemIconBox}>
              <Feather name="map-pin" size={20} color="#00875A" />
            </View>
            <View style={styles.itemInfo}>
              <Text style={styles.itemTitle}>Cached locations</Text>
              <Text style={styles.itemSub}>12 assigned inspection sites</Text>
            </View>
            <View style={styles.readyBadge}>
              <Text style={styles.readyBadgeText}>Ready</Text>
            </View>
          </View>

          <View style={styles.itemDivider} />

          {/* Item 3: Pending reports */}
          <View style={styles.availableItem}>
            <View style={styles.itemIconBox}>
              <Feather name="clock" size={20} color="#00875A" />
            </View>
            <View style={styles.itemInfo}>
              <Text style={styles.itemTitle}>Pending reports</Text>
              <Text style={styles.itemSub}>3 reports • 8 photos attached</Text>
            </View>
            <View style={styles.queuedBadge}>
              <Text style={styles.queuedBadgeText}>Queued</Text>
            </View>
          </View>
        </View>

        {/* Storage Bar Card */}
        <View style={styles.storageCard}>
          <View style={styles.storageHeaderRow}>
            <Text style={styles.storageLabel}>Offline storage</Text>
            <Text style={styles.storageStats}>286 MB / 1 GB</Text>
          </View>

          <View style={styles.progressTrack}>
            <View style={[styles.progressFill, { width: '28.6%' }]} />
          </View>

          <Text style={styles.storageFootnote}>Your downloaded maps are up to date.</Text>
        </View>

        {/* Last Sync Card */}
        <View style={styles.lastSyncCard}>
          <View style={styles.syncIconCircle}>
            <Feather name="cloud" size={20} color="#00875A" />
          </View>
          <View style={styles.syncInfoCol}>
            <Text style={styles.lastSyncLabel}>Last successful sync</Text>
            <Text style={styles.lastSyncTime}>{lastSync}</Text>
          </View>
        </View>

        {/* Sync Now Button */}
        <TouchableOpacity
          style={styles.syncNowBtn}
          onPress={handleSyncNow}
          disabled={syncing}
          activeOpacity={0.85}>
          <Feather
            name={syncing ? 'loader' : 'rotate-cw'}
            size={18}
            color="#334155"
          />
          <Text style={styles.syncNowBtnText}>
            {syncing ? 'Syncing...' : 'Sync Now'}
          </Text>
        </TouchableOpacity>

        {/* Subtext info */}
        <Text style={styles.reconnectNotice}>
          Reconnect to Wi-Fi or mobile data to sync. Auto-sync will resume when a connection is available.
        </Text>

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
    paddingBottom: 40,
  },
  offlineAlertCard: {
    backgroundColor: '#FFFBEB',
    borderWidth: 1,
    borderColor: '#FDE68A',
    borderRadius: 20,
    padding: 18,
    flexDirection: 'row',
    gap: 14,
    marginBottom: 24,
  },
  offlineIconBox: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#FEF3C7',
    alignItems: 'center',
    justifyContent: 'center',
  },
  offlineTextCol: {
    flex: 1,
  },
  offlineTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#92400E',
  },
  offlineSubTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#B45309',
    marginTop: 2,
    marginBottom: 6,
  },
  offlineDesc: {
    fontSize: 12,
    color: '#78350F',
    lineHeight: 18,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#0F172A',
    marginBottom: 12,
  },
  availableList: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    paddingHorizontal: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 20,
  },
  availableItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    gap: 12,
  },
  itemIconBox: {
    width: 36,
    height: 36,
    borderRadius: 12,
    backgroundColor: '#E8F5E9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  itemInfo: {
    flex: 1,
  },
  itemTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
  },
  itemSub: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
  readyBadge: {
    backgroundColor: '#D1FAE5',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  readyBadgeText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#065F46',
  },
  queuedBadge: {
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  queuedBadgeText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#B45309',
  },
  itemDivider: {
    height: 1,
    backgroundColor: '#F8FAFC',
  },
  storageCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 18,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 16,
  },
  storageHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  storageLabel: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
  },
  storageStats: {
    fontSize: 13,
    fontWeight: '700',
    color: '#64748B',
  },
  progressTrack: {
    height: 8,
    backgroundColor: '#F1F5F9',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 10,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#00875A',
  },
  storageFootnote: {
    fontSize: 12,
    color: '#64748B',
  },
  lastSyncCard: {
    backgroundColor: '#ECFDF5',
    borderRadius: 18,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    borderWidth: 1,
    borderColor: '#A7F3D0',
    marginBottom: 16,
  },
  syncIconCircle: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  syncInfoCol: {
    flex: 1,
  },
  lastSyncLabel: {
    fontSize: 12,
    color: '#065F46',
    fontWeight: '600',
  },
  lastSyncTime: {
    fontSize: 14,
    fontWeight: '800',
    color: '#065F46',
    marginTop: 2,
  },
  syncNowBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    height: 50,
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
    gap: 8,
    marginBottom: 14,
  },
  syncNowBtnText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
  },
  reconnectNotice: {
    textAlign: 'center',
    fontSize: 11,
    color: '#94A3B8',
    lineHeight: 16,
    paddingHorizontal: 10,
  },
});

