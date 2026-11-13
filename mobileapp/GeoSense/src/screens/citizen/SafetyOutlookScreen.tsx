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

export function SafetyOutlookScreen() {
  const { navigate } = useApp();
  const [selectedHorizon, setSelectedHorizon] = useState('Next 6 Hours');

  const recommendations = [
    'Avoid steep slopes',
    'Stay away from unstable roads',
    'Keep emergency essentials ready',
    'Follow official evacuation instructions',
  ];

  return (
    <SafeAreaView style={styles.safeArea}>
      <HeaderBar
        title="Your safety outlook"
        subtitle="Dashboard · Continued"
        variant="sub-light"
      />

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}>
        
        {/* Risk Forecast */}
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionTitle}>Risk Forecast</Text>
          <TouchableOpacity onPress={() => navigate('location-details')} activeOpacity={0.7}>
            <Text style={styles.headerLink}>View details</Text>
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

        {/* 4 Forecast Cards */}
        <View style={styles.timelineRow}>
          <View style={styles.timelineCard}>
            <Text style={styles.timelineTime}>Now</Text>
            <Text style={[styles.timelineVal, { color: '#EF4444' }]}>82%</Text>
          </View>
          <View style={[styles.timelineCard, styles.timelineCardHighlight]}>
            <Text style={styles.timelineTime}>6h</Text>
            <Text style={[styles.timelineVal, { color: '#EF4444' }]}>87%</Text>
          </View>
          <View style={styles.timelineCard}>
            <Text style={styles.timelineTime}>24h</Text>
            <Text style={[styles.timelineVal, { color: '#EF4444' }]}>74%</Text>
          </View>
          <View style={styles.timelineCard}>
            <Text style={styles.timelineTime}>7d</Text>
            <Text style={[styles.timelineVal, { color: '#F59E0B' }]}>58%</Text>
          </View>
        </View>
        <Text style={styles.captionText}>
          Illustrative model outlook · Risk may change rapidly.
        </Text>

        {/* Weather overview */}
        <View style={[styles.sectionHeaderRow, { marginTop: 24 }]}>
          <Text style={styles.sectionTitle}>Weather overview</Text>
          <Text style={styles.updatedText}>Updated 5m ago</Text>
        </View>

        <View style={styles.weatherCard}>
          <View style={styles.weatherTopRow}>
            <View style={styles.weatherInfo}>
              <View style={styles.weatherIconCircle}>
                <Feather name="cloud-rain" size={26} color="#00875A" />
              </View>
              <View>
                <Text style={styles.weatherCondition}>Heavy rainfall</Text>
                <Text style={styles.weatherLocation}>Cherrapunji · Monsoon conditions</Text>
              </View>
            </View>
            <Text style={styles.weatherTemp}>19°</Text>
          </View>

          <View style={styles.weatherDivider} />

          <View style={styles.weatherStatsRow}>
            <View style={styles.weatherStatCol}>
              <Text style={styles.statValue}>112 mm</Text>
              <Text style={styles.statLabel}>Rain / 24h</Text>
            </View>
            <View style={styles.statBorderDivider} />
            <View style={styles.weatherStatCol}>
              <Text style={styles.statValue}>96%</Text>
              <Text style={styles.statLabel}>Humidity</Text>
            </View>
            <View style={styles.statBorderDivider} />
            <View style={styles.weatherStatCol}>
              <Text style={styles.statValue}>12 mm/h</Text>
              <Text style={styles.statLabel}>Intensity</Text>
            </View>
          </View>
        </View>

        {/* Safety recommendations */}
        <View style={[styles.sectionHeaderRow, { marginTop: 26 }]}>
          <Text style={styles.sectionTitle}>Safety recommendations</Text>
        </View>

        <View style={styles.recommendationsList}>
          {recommendations.map((item, idx) => (
            <View key={idx} style={styles.recommendationItem}>
              <View style={styles.checkIconBox}>
                <Feather name="shield" size={18} color="#00875A" />
              </View>
              <Text style={styles.recommendationText}>{item}</Text>
            </View>
          ))}
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
    paddingBottom: 40,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0F172A',
  },
  headerLink: {
    fontSize: 14,
    fontWeight: '600',
    color: '#00875A',
  },
  updatedText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#00875A',
  },
  horizonScroll: {
    marginBottom: 16,
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
  timelineRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 10,
    marginBottom: 10,
  },
  timelineCard: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    paddingVertical: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  timelineCardHighlight: {
    borderColor: '#EF4444',
    borderWidth: 1.5,
  },
  timelineTime: {
    fontSize: 13,
    fontWeight: '600',
    color: '#64748B',
    marginBottom: 4,
  },
  timelineVal: {
    fontSize: 22,
    fontWeight: '800',
  },
  captionText: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
  weatherCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
    elevation: 2,
    borderWidth: 1,
    borderColor: '#F1F5F9',
  },
  weatherTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  weatherInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
  },
  weatherIconCircle: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#E8F5E9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  weatherCondition: {
    fontSize: 17,
    fontWeight: '700',
    color: '#0F172A',
  },
  weatherLocation: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
  weatherTemp: {
    fontSize: 32,
    fontWeight: '700',
    color: '#0F172A',
  },
  weatherDivider: {
    height: 1,
    backgroundColor: '#F1F5F9',
    marginVertical: 16,
  },
  weatherStatsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  weatherStatCol: {
    flex: 1,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#0F172A',
  },
  statLabel: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
  statBorderDivider: {
    width: 1,
    height: 28,
    backgroundColor: '#E2E8F0',
  },
  recommendationsList: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderWidth: 1,
    borderColor: '#F1F5F9',
  },
  recommendationItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#F8FAFC',
  },
  checkIconBox: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#E8F5E9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  recommendationText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#1E293B',
    flex: 1,
  },
});

