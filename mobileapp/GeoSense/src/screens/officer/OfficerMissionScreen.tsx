import { SafeAreaView } from 'react-native-safe-area-context';
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  Alert,
} from 'react-native';
import { Feather, Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { HeaderBar } from '@/components/HeaderBar';
import { useApp } from '@/context/AppContext';

export function OfficerMissionScreen() {
  const { navigate } = useApp();
  const [navigating, setNavigating] = useState(false);

  return (
    <SafeAreaView style={styles.safeArea} edges={['left', 'right']}>
      <HeaderBar
        title="Assigned Mission"
        subtitle="MISSION GS-2048"
        variant="officer-dark"
      />

      <View style={styles.container}>
        {/* Map Viewport with Mission Route */}
        <View style={styles.mapViewport}>
          <Image
            source={require('@/assets/images/design/mission_map.jpg')}
            style={StyleSheet.absoluteFill}
            resizeMode="cover"
          />
            
            {/* Destination Flag Tag */}
            <View style={styles.destinationTag}>
              <Text style={styles.destinationTagText}>Sohra slope · S1</Text>
            </View>

            {/* Flag Pin */}
            <View style={styles.flagPin}>
              <Feather name="flag" size={18} color="#FFFFFF" />
            </View>

            {/* Map Tools Right */}
            <View style={styles.mapTools}>
              <TouchableOpacity style={styles.toolBtn}>
                <MaterialCommunityIcons name="layers-outline" size={20} color="#1E293B" />
              </TouchableOpacity>
              <TouchableOpacity style={styles.toolBtn}>
                <Feather name="crosshair" size={20} color="#1E293B" />
              </TouchableOpacity>
            </View>

            {/* Map Legend */}
            <View style={styles.mapLegend}>
              <View style={styles.legendItem}>
                <View style={[styles.legendDot, { backgroundColor: '#EF4444' }]} />
                <Text style={styles.legendLabel}>High risk</Text>
              </View>
              <View style={styles.legendItem}>
                <View style={[styles.legendDot, { backgroundColor: '#F59E0B' }]} />
                <Text style={styles.legendLabel}>Moderate</Text>
              </View>
              <View style={styles.legendItem}>
                <View style={[styles.legendDot, { backgroundColor: '#3B82F6' }]} />
                <Text style={styles.legendLabel}>Route</Text>
              </View>
            </View>
        </View>

        {/* Bottom Mission Card */}
        <View style={styles.missionCard}>
          <View style={styles.missionCardHeader}>
            <View>
              <Text style={styles.missionName}>Sohra slope · S1</Text>
              <Text style={styles.missionType}>On-site inspection & risk assessment</Text>
            </View>
            <View style={styles.priorityBadge}>
              <Text style={styles.priorityBadgeText}>High priority</Text>
            </View>
          </View>

          {/* 3 Metric Cards */}
          <View style={styles.metricsRow}>
            <View style={styles.metricCard}>
              <Feather name="navigation" size={18} color="#00875A" />
              <View>
                <Text style={styles.metricVal}>2.8 km</Text>
                <Text style={styles.metricLabel}>Distance</Text>
              </View>
            </View>

            <View style={styles.metricCard}>
              <Feather name="clock" size={18} color="#00875A" />
              <View>
                <Text style={styles.metricVal}>8 min</Text>
                <Text style={styles.metricLabel}>ETA</Text>
              </View>
            </View>

            <View style={styles.metricCard}>
              <MaterialCommunityIcons name="routes" size={18} color="#00875A" />
              <View>
                <Text style={styles.metricVal}>Via SH-5</Text>
                <Text style={styles.metricLabel}>Route</Text>
              </View>
            </View>
          </View>

          {/* Assigned Time */}
          <View style={styles.assignedTimeRow}>
            <Feather name="calendar" size={16} color="#64748B" />
            <Text style={styles.assignedTimeText}>Assigned today at 09:00 AM</Text>
          </View>

          {/* Instructions Box */}
          <View style={styles.instructionsRow}>
            <Feather name="check-square" size={16} color="#64748B" />
            <Text style={styles.instructionsText}>
              Inspect slope stability, capture evidence and validate the AI risk assessment.
            </Text>
          </View>

          {/* Start Navigation */}
          <TouchableOpacity
            style={[
              styles.startNavBtn,
              navigating && { backgroundColor: '#0D5C3A' },
            ]}
            onPress={() => {
              setNavigating(!navigating);
            }}
            activeOpacity={0.85}>
            <Feather name="navigation" size={18} color="#FFFFFF" />
            <Text style={styles.startNavBtnText}>
              {navigating ? 'Navigation Active' : 'Start Navigation'}
            </Text>
          </TouchableOpacity>

          <Text style={styles.safetyDisclaimer}>
            Stay outside marked risk zones during inspection.
          </Text>
        </View>
      </View>
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
  mapViewport: {
    flex: 1,
  },
  mapImage: {
    flex: 1,
    position: 'relative',
  },
  destinationTag: {
    position: 'absolute',
    top: '12%',
    left: '38%',
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 14,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
  },
  destinationTagText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#0F172A',
  },
  flagPin: {
    position: 'absolute',
    top: '16%',
    right: '28%',
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: '#00875A',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: '#FFFFFF',
  },
  mapTools: {
    position: 'absolute',
    top: '10%',
    right: 16,
    gap: 8,
  },
  toolBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  mapLegend: {
    position: 'absolute',
    bottom: 16,
    left: 16,
    backgroundColor: '#FFFFFF',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 14,
    gap: 12,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  legendDot: {
    width: 7,
    height: 7,
    borderRadius: 3.5,
  },
  legendLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: '#334155',
  },
  missionCard: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -3 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 8,
  },
  missionCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  missionName: {
    fontSize: 22,
    fontWeight: '800',
    color: '#0F172A',
  },
  missionType: {
    fontSize: 13,
    color: '#64748B',
    marginTop: 2,
  },
  priorityBadge: {
    backgroundColor: '#FEE2E2',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  priorityBadgeText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#DC2626',
  },
  metricsRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 16,
  },
  metricCard: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 14,
    padding: 10,
    gap: 8,
  },
  metricVal: {
    fontSize: 13,
    fontWeight: '800',
    color: '#0F172A',
  },
  metricLabel: {
    fontSize: 10,
    color: '#64748B',
  },
  assignedTimeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 10,
  },
  assignedTimeText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#334155',
  },
  instructionsRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    marginBottom: 18,
  },
  instructionsText: {
    fontSize: 13,
    color: '#475569',
    flex: 1,
    lineHeight: 18,
  },
  startNavBtn: {
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
    marginBottom: 10,
  },
  startNavBtnText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  safetyDisclaimer: {
    textAlign: 'center',
    fontSize: 11,
    color: '#94A3B8',
  },
});

