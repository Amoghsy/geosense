import { SafeAreaView } from 'react-native-safe-area-context';
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import {
  Feather,
  MaterialCommunityIcons,
  Ionicons,
} from '@expo/vector-icons';
import { useApp } from '@/context/AppContext';
import { HeaderBar } from '@/components/HeaderBar';

export function CitizenHomeScreen() {
  const { navigate } = useApp();
  const [selectedHorizon, setSelectedHorizon] = useState('Next 6 Hours');
  const [isBannerOpen, setIsBannerOpen] = useState(false);

  return (
    <SafeAreaView style={styles.safeArea} edges={['left', 'right']}>
      <HeaderBar variant="citizen-main" />

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}>
        
        {/* Greeting & Location */}
        <View style={styles.greetingSection}>
          <Text style={styles.greetingTitle}>Hello, Welcome Back!</Text>
          <TouchableOpacity
            style={styles.locationSelector}
            onPress={() => navigate('map')}
            activeOpacity={0.7}>
            <Ionicons name="location-outline" size={18} color="#00875A" />
            <Text style={styles.locationText}>Cherrapunji, Meghalaya</Text>
            <Feather name="chevron-down" size={16} color="#00875A" />
          </TouchableOpacity>
        </View>

        {/* Current Risk Banner Card */}
        <TouchableOpacity
          activeOpacity={0.92}
          onPress={() => navigate('location-details')}
          style={styles.riskCard}>
          <View style={styles.riskCardHeader}>
            <View style={styles.riskTagLeft}>
              <Ionicons name="warning-outline" size={18} color="#FFFFFF" />
              <Text style={styles.riskTagLabel}>CURRENT RISK</Text>
            </View>
            <View style={styles.highBadge}>
              <Text style={styles.highBadgeText}>HIGH</Text>
            </View>
          </View>

          <View style={styles.riskValueRow}>
            <Text style={styles.riskPercentage}>87%</Text>
            <View style={styles.riskSubInfo}>
              <Text style={styles.riskSubtitle}>Landslide probability</Text>
              <Text style={styles.riskWindow}>Next 6 Hours</Text>
            </View>
          </View>

          <View style={styles.riskCardFooter}>
            <View style={styles.trendRow}>
              <Feather name="trending-up" size={16} color="#FFFFFF" />
              <Text style={styles.trendText}>Increasing</Text>
            </View>
            <Text style={styles.updatedText}>Last Updated 5 minutes ago</Text>
          </View>
        </TouchableOpacity>

        {/* Quick Actions */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
        </View>

        <View style={styles.quickActionsGrid}>
          {/* 1. Risk Map */}
          <TouchableOpacity
            style={styles.actionCard}
            onPress={() => navigate('map')}
            activeOpacity={0.75}>
            <View style={styles.actionIconBox}>
              <Feather name="map" size={24} color="#00875A" />
            </View>
            <Text style={styles.actionLabel}>Risk Map</Text>
          </TouchableOpacity>

          {/* 2. Offline Maps */}
          <TouchableOpacity
            style={styles.actionCard}
            onPress={() => navigate('offline-maps')}
            activeOpacity={0.75}>
            <View style={styles.actionIconBox}>
              <Feather name="download" size={24} color="#00875A" />
            </View>
            <Text style={styles.actionLabel}>Offline Maps</Text>
          </TouchableOpacity>

          {/* 3. Evacuation */}
          <TouchableOpacity
            style={styles.actionCard}
            onPress={() => navigate('evacuation')}
            activeOpacity={0.75}>
            <View style={styles.actionIconBox}>
              <MaterialCommunityIcons name="call-split" size={24} color="#00875A" />
            </View>
            <Text style={styles.actionLabel}>Evacuation</Text>
          </TouchableOpacity>

          {/* 4. Report Incident */}
          <TouchableOpacity
            style={styles.actionCard}
            onPress={() => navigate('report-incident-1')}
            activeOpacity={0.75}>
            <View style={styles.actionIconBox}>
              <Feather name="camera" size={24} color="#00875A" />
            </View>
            <Text style={styles.actionLabel}>Report Incident</Text>
          </TouchableOpacity>

          {/* 5. Nearby Resources */}
          <TouchableOpacity
            style={styles.actionCard}
            onPress={() => navigate('resources')}
            activeOpacity={0.75}>
            <View style={styles.actionIconBox}>
              <MaterialCommunityIcons name="hospital-box-outline" size={24} color="#00875A" />
            </View>
            <Text style={styles.actionLabel}>Nearby Resources</Text>
          </TouchableOpacity>

          {/* 6. Weather */}
          <TouchableOpacity
            style={styles.actionCard}
            onPress={() => navigate('safety-outlook')}
            activeOpacity={0.75}>
            <View style={styles.actionIconBox}>
              <Feather name="cloud-rain" size={24} color="#00875A" />
            </View>
            <Text style={styles.actionLabel}>Weather</Text>
          </TouchableOpacity>
        </View>

        {/* Risk Forecast Section */}
        <View style={styles.forecastHeaderRow}>
          <Text style={styles.sectionTitle}>Risk Forecast</Text>
          <TouchableOpacity
            onPress={() => navigate('safety-outlook')}
            style={styles.safetyOutlookLink}
            activeOpacity={0.7}>
            <Text style={styles.safetyOutlookText}>Safety outlook</Text>
            <Feather name="arrow-right" size={16} color="#00875A" />
          </TouchableOpacity>
        </View>

        {/* Horizon selector tabs */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.horizonScroll}
          contentContainerStyle={styles.horizonContainer}>
          {['Current Risk', 'Next 6 Hours', 'Next 24 Hours', 'Next 7 Days'].map((h) => {
            const isSelected = selectedHorizon === h;
            return (
              <TouchableOpacity
                key={h}
                onPress={() => setSelectedHorizon(h)}
                style={[
                  styles.horizonPill,
                  isSelected && styles.horizonPillActive,
                ]}>
                <Text
                  style={[
                    styles.horizonPillText,
                    isSelected && styles.horizonPillTextActive,
                  ]}>
                  {h}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        {/* Collapsible Info Banner */}
        <TouchableOpacity
          style={styles.bannerRow}
          onPress={() => {
            setIsBannerOpen(!isBannerOpen);
            navigate('safety-outlook');
          }}
          activeOpacity={0.8}>
          <Text style={styles.bannerText}>
            6h peak: 87% · Weather & safety below
          </Text>
          <Feather
            name={isBannerOpen ? 'chevron-up' : 'chevron-down'}
            size={18}
            color="#00875A"
          />
        </TouchableOpacity>

        {/* Demo Disclaimer */}
        <View style={styles.disclaimerBox}>
          <Text style={styles.disclaimerText}>Demo data · Not a live safety advisory</Text>
        </View>

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
    paddingBottom: 90,
  },
  greetingSection: {
    marginBottom: 20,
  },
  greetingTitle: {
    fontSize: 26,
    fontWeight: '800',
    color: '#0F172A',
    letterSpacing: -0.5,
  },
  locationSelector: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 8,
  },
  locationText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#00875A',
  },
  riskCard: {
    backgroundColor: '#EA3838',
    borderRadius: 24,
    padding: 22,
    shadowColor: '#EA3838',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.25,
    shadowRadius: 16,
    elevation: 6,
    marginBottom: 24,
  },
  riskCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  riskTagLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  riskTagLabel: {
    fontSize: 13,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: 0.8,
  },
  highBadge: {
    borderWidth: 1.5,
    borderColor: 'rgba(255,255,255,0.7)',
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingVertical: 3,
    backgroundColor: 'rgba(255,255,255,0.15)',
  },
  highBadgeText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  riskValueRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 14,
    marginTop: 18,
    marginBottom: 16,
  },
  riskPercentage: {
    fontSize: 58,
    fontWeight: '900',
    color: '#FFFFFF',
    lineHeight: 64,
  },
  riskSubInfo: {
    paddingBottom: 6,
  },
  riskSubtitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  riskWindow: {
    fontSize: 14,
    fontWeight: '500',
    color: 'rgba(255,255,255,0.85)',
    marginTop: 2,
  },
  riskCardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.2)',
    paddingTop: 12,
  },
  trendRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  trendText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '600',
  },
  updatedText: {
    color: 'rgba(255,255,255,0.8)',
    fontSize: 12,
  },
  sectionHeader: {
    marginBottom: 14,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0F172A',
    letterSpacing: -0.2,
  },
  quickActionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    rowGap: 14,
    marginBottom: 26,
  },
  actionCard: {
    width: '31%',
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    paddingVertical: 16,
    paddingHorizontal: 4,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
    elevation: 2,
    borderWidth: 1,
    borderColor: '#F1F5F9',
  },
  actionIconBox: {
    width: 46,
    height: 46,
    borderRadius: 14,
    backgroundColor: '#E8F5E9',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  actionLabel: {
    fontSize: 11.5,
    fontWeight: '600',
    color: '#334155',
    textAlign: 'center',
    lineHeight: 15,
  },
  forecastHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
  },
  safetyOutlookLink: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  safetyOutlookText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#00875A',
  },
  horizonScroll: {
    marginBottom: 14,
  },
  horizonContainer: {
    gap: 8,
    backgroundColor: '#F1F5F9',
    padding: 4,
    borderRadius: 14,
  },
  horizonPill: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 10,
  },
  horizonPillActive: {
    backgroundColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  horizonPillText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#64748B',
  },
  horizonPillTextActive: {
    color: '#0F172A',
    fontWeight: '700',
  },
  bannerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#ECFDF5',
    borderWidth: 1,
    borderColor: '#A7F3D0',
    borderRadius: 16,
    paddingVertical: 14,
    paddingHorizontal: 16,
    marginBottom: 20,
  },
  bannerText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#065F46',
  },
  disclaimerBox: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    paddingVertical: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  disclaimerText: {
    fontSize: 12,
    color: '#64748B',
    fontWeight: '500',
  },
});
