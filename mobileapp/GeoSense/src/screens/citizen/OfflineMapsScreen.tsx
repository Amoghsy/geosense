import { SafeAreaView } from 'react-native-safe-area-context';
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  Alert,
} from 'react-native';
import { Feather, Ionicons } from '@expo/vector-icons';
import { HeaderBar } from '@/components/HeaderBar';
import { geoSenseApi } from '@/services/api';

export function OfflineMapsScreen() {
  const [syncTime, setSyncTime] = useState('Not synced yet');
  const [isSyncing, setIsSyncing] = useState(false);

  const handleSync = async () => {
    setIsSyncing(true);
    try {
      const summary = await geoSenseApi.getGisSummary();
      setSyncTime(`Synced · ${new Date().toLocaleTimeString()}`);
      Alert.alert(
        'Synchronized',
        `GIS summary synced (${summary?.total_risk_locations ?? 0} risk locations, ${summary?.total_resources ?? 0} resources).`
      );
    } catch {
      Alert.alert('Sync Failed', 'Unable to reach GeoSense backend server.');
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['left', 'right']}>
      <HeaderBar
        title="Offline Maps"
        subtitle="Prepared, even without a signal"
        variant="sub-light"
      />

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}>
        
        {/* Connection Status Card */}
        <View style={styles.statusCard}>
          <View style={styles.statusHeaderRow}>
            <View style={styles.statusLeft}>
              <Feather name="wifi" size={18} color="#065F46" />
              <Text style={styles.statusLabel}>Connection Status</Text>
            </View>
            <Text style={styles.connectedBadge}>Connected</Text>
          </View>
          <Text style={styles.statusDesc}>
            Your saved safety information is ready offline.
          </Text>
        </View>

        {/* Downloaded Map Card with scenic image */}
        <View style={styles.mapCard}>
          <View style={styles.mapImageWrapper}>
            <Image
              source={require('@/assets/images/design/meghalaya_mountains.jpg')}
              style={styles.mapThumb}
              resizeMode="cover"
            />
            <View style={styles.downloadedPill}>
              <View style={styles.greenDot} />
              <Text style={styles.downloadedPillText}>DOWNLOADED</Text>
            </View>
          </View>

          <View style={styles.mapCardBody}>
            <View style={styles.mapTitleRow}>
              <Text style={styles.mapName}>Meghalaya</Text>
              <Text style={styles.mapFileSize}>128 MB</Text>
            </View>

            {/* Progress bar (100%) */}
            <View style={styles.progressTrack}>
              <View style={[styles.progressFill, { width: '100%' }]} />
            </View>

            <View style={styles.progressLabelRow}>
              <Text style={styles.progressStatusText}>Download complete</Text>
              <Text style={styles.progressPercentageText}>100%</Text>
            </View>
          </View>
        </View>

        {/* Offline Readiness Section */}
        <Text style={styles.sectionTitle}>Offline readiness</Text>

        <View style={styles.readinessCard}>
          <View style={styles.syncRow}>
            <Text style={styles.syncLabel}>Last Data Synchronization</Text>
            <Text style={styles.syncTimestamp}>{syncTime}</Text>
          </View>

          <View style={styles.divider} />

          <View style={styles.cachedInfoSection}>
            <Text style={styles.cachedLabel}>Cached Safety Information</Text>
            <Text style={styles.cachedDesc}>
              5 resources · Safe routes · Emergency contacts Latest saved warnings & evacuation guidelines
            </Text>
          </View>
        </View>

        {/* Warning callout */}
        <View style={styles.warningCard}>
          <Feather name="info" size={16} color="#D97706" />
          <Text style={styles.warningText}>
            Offline maps do not provide live risk updates. Reconnect to refresh advisories before travelling.
          </Text>
        </View>

        {/* Synchronize Now Button */}
        <TouchableOpacity
          style={styles.syncButton}
          onPress={handleSync}
          disabled={isSyncing}
          activeOpacity={0.85}>
          <Feather
            name={isSyncing ? 'loader' : 'rotate-cw'}
            size={18}
            color="#FFFFFF"
          />
          <Text style={styles.syncButtonText}>
            {isSyncing ? 'Synchronizing...' : 'Synchronize now'}
          </Text>
        </TouchableOpacity>

      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#FFFFFF',
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
  statusCard: {
    backgroundColor: '#ECFDF5',
    borderWidth: 1,
    borderColor: '#A7F3D0',
    borderRadius: 16,
    padding: 16,
    marginBottom: 20,
  },
  statusHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  statusLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  statusLabel: {
    fontSize: 14,
    fontWeight: '700',
    color: '#065F46',
  },
  connectedBadge: {
    fontSize: 13,
    fontWeight: '700',
    color: '#00875A',
  },
  statusDesc: {
    fontSize: 12,
    color: '#047857',
    marginTop: 2,
  },
  mapCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
    elevation: 2,
  },
  mapImageWrapper: {
    height: 140,
    position: 'relative',
  },
  mapThumb: {
    width: '100%',
    height: '100%',
  },
  downloadedPill: {
    position: 'absolute',
    top: 12,
    left: 12,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(15, 23, 42, 0.8)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 6,
  },
  greenDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#10B981',
  },
  downloadedPillText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  mapCardBody: {
    padding: 16,
  },
  mapTitleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  mapName: {
    fontSize: 18,
    fontWeight: '800',
    color: '#0F172A',
  },
  mapFileSize: {
    fontSize: 13,
    fontWeight: '600',
    color: '#64748B',
  },
  progressTrack: {
    height: 6,
    backgroundColor: '#F1F5F9',
    borderRadius: 3,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#00875A',
  },
  progressLabelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  progressStatusText: {
    fontSize: 12,
    color: '#64748B',
  },
  progressPercentageText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#0F172A',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 12,
  },
  readinessCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 18,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 16,
  },
  syncRow: {
    marginBottom: 12,
  },
  syncLabel: {
    fontSize: 12,
    color: '#64748B',
    marginBottom: 2,
  },
  syncTimestamp: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
  },
  divider: {
    height: 1,
    backgroundColor: '#F1F5F9',
    marginBottom: 12,
  },
  cachedInfoSection: {},
  cachedLabel: {
    fontSize: 12,
    color: '#64748B',
    marginBottom: 4,
  },
  cachedDesc: {
    fontSize: 13,
    color: '#334155',
    lineHeight: 18,
  },
  warningCard: {
    flexDirection: 'row',
    backgroundColor: '#FFFBEB',
    borderWidth: 1,
    borderColor: '#FDE68A',
    borderRadius: 14,
    padding: 14,
    gap: 10,
    marginBottom: 24,
  },
  warningText: {
    fontSize: 12,
    color: '#92400E',
    lineHeight: 18,
    flex: 1,
  },
  syncButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#00875A',
    borderRadius: 16,
    height: 52,
    gap: 8,
    shadowColor: '#00875A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 3,
  },
  syncButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
});

