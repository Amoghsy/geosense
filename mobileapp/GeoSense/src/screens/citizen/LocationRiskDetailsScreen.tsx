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

export function LocationRiskDetailsScreen() {
  const { navigate, selectedLocation, setLatestAssessmentId } = useApp();
  const [selectedRange, setSelectedRange] = useState('1–6 Hours');
  const [riskData, setRiskData] = useState<any | null>(null);
  const [latestRecord, setLatestRecord] = useState<any | null>(null);
  const [rainfallData, setRainfallData] = useState<any | null>(null);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const risk = await geoSenseApi.getCitizenRisk(
          selectedLocation.latitude,
          selectedLocation.longitude,
          selectedLocation.name
        );
        if (!active) return;
        setRiskData(risk);

        if (risk?.location_id) {
          const [latest, rain] = await Promise.all([
            geoSenseApi.getLatestRisk(risk.location_id).catch(() => null),
            geoSenseApi
              .getRainfallIndicators(
                selectedLocation.latitude,
                selectedLocation.longitude,
                risk.location_id
              )
              .catch(() => null),
          ]);
          if (!active) return;
          if (latest) {
            setLatestRecord(latest);
            if (latest.assessment_id) {
              setLatestAssessmentId(latest.assessment_id);
            }
          }
          if (rain) setRainfallData(rain);
        }
      } catch {
        // leave null
      }
    };
    load();
    return () => {
      active = false;
    };
  }, [selectedLocation.latitude, selectedLocation.longitude, selectedLocation.name]);

  const rain24h =
    riskData?.recent_rainfall_24h_mm ??
    rainfallData?.observed_windows?.['24h']?.rainfall_mm ??
    latestRecord?.rainfall_24h_mm;
  const forecast24h =
    riskData?.forecast_rainfall_24h_mm ??
    rainfallData?.forecast_windows?.next_24h?.rainfall_mm ??
    latestRecord?.forecast_24h_mm;
  const slopeDeg = latestRecord?.slope_deg;
  const soilMoist = latestRecord?.soil_moisture_m3_m3;
  const awi = rainfallData?.awi_value;

  const factors = [
    {
      icon: <Feather name="cloud-rain" size={20} color="#00875A" />,
      label: 'Observed Rainfall (24h)',
      value: rain24h !== null && rain24h !== undefined ? `${Number(rain24h).toFixed(1)} mm` : 'N/A',
    },
    {
      icon: <Feather name="cloud-lightning" size={20} color="#00875A" />,
      label: 'Forecast Rainfall (24h)',
      value: forecast24h !== null && forecast24h !== undefined ? `${Number(forecast24h).toFixed(1)} mm` : 'N/A',
    },
    {
      icon: <MaterialCommunityIcons name="triangle-outline" size={20} color="#00875A" />,
      label: 'Slope Angle',
      value: slopeDeg !== null && slopeDeg !== undefined ? `${slopeDeg}°` : 'Terrain DEM',
    },
    {
      icon: <Feather name="droplet" size={20} color="#00875A" />,
      label: 'Soil Moisture',
      value: soilMoist !== null && soilMoist !== undefined ? `${Number(soilMoist).toFixed(2)} m³/m³` : 'Monitored',
    },
    {
      icon: <Feather name="clock" size={20} color="#00875A" />,
      label: 'Antecedent Wetness (AWI)',
      value: awi !== null && awi !== undefined ? `${Number(awi).toFixed(1)} mm` : 'Computed',
    },
  ];

  const latStr = `${Math.abs(selectedLocation.latitude).toFixed(4)}° ${selectedLocation.latitude >= 0 ? 'N' : 'S'}`;
  const lonStr = `${Math.abs(selectedLocation.longitude).toFixed(4)}° ${selectedLocation.longitude >= 0 ? 'E' : 'W'}`;
  const scoreDisplay =
    riskData?.risk_score !== null && riskData?.risk_score !== undefined
      ? `${Math.round(riskData.risk_score)}%`
      : '--';
  const catDisplay = riskData?.risk_category || 'LOADING';

  return (
    <SafeAreaView style={styles.safeArea} edges={['left', 'right']}>
      <HeaderBar title="Location Risk Details" variant="sub-light" />

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}>
        
        {/* Location Title & Subtitle */}
        <View style={styles.locationHeader}>
          <Text style={styles.locationName}>{selectedLocation.name}</Text>
          <View style={styles.coordsRow}>
            <Text style={styles.coordsText}>{latStr}, {lonStr}</Text>
            <Text style={styles.updatedText}>
              {riskData?.assessment_time ? `Updated ${formatRelativeTime(riskData.assessment_time)}` : 'Syncing...'}
            </Text>
          </View>
        </View>

        {/* High Risk Status Card */}
        <View style={styles.riskCard}>
          <View style={styles.riskCardHeader}>
            <View style={styles.highRiskPill}>
              <View style={styles.redDot} />
              <Text style={styles.highRiskText}>{catDisplay} RISK</Text>
            </View>
            <View style={styles.trendRow}>
              <Feather name="activity" size={14} color="#EF4444" />
              <Text style={styles.trendText}>Live Model</Text>
            </View>
          </View>

          <View style={styles.riskValuesRow}>
            <Text style={styles.percentageText}>{scoreDisplay}</Text>
            <View style={styles.labelsCol}>
              <Text style={styles.probabilityLabel}>Dynamic risk index</Text>
              <Text style={styles.windowLabel}>{selectedRange}</Text>
            </View>
          </View>
        </View>

        {/* Time Horizon Segmented Tabs */}
        <View style={styles.rangeTabsContainer}>
          {['Current', '1–6 Hours', '1–7 Days', 'Weekly'].map((r) => {
            const isSelected = selectedRange === r;
            return (
              <TouchableOpacity
                key={r}
                onPress={() => setSelectedRange(r)}
                style={[
                  styles.rangeTab,
                  isSelected && styles.rangeTabActive,
                ]}>
                <Text
                  style={[
                    styles.rangeTabText,
                    isSelected && styles.rangeTabTextActive,
                  ]}>
                  {r}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>

        {/* Environmental Factors */}
        <Text style={styles.sectionTitle}>Environmental factors</Text>

        <View style={styles.factorsList}>
          {factors.map((item, idx) => (
            <View key={idx} style={styles.factorRow}>
              <View style={styles.factorLeft}>
                <View style={styles.iconCircle}>{item.icon}</View>
                <Text style={styles.factorLabel}>{item.label}</Text>
              </View>
              <Text style={styles.factorValue}>{item.value}</Text>
            </View>
          ))}
        </View>

        {/* Why is this area at risk? CTA */}
        <TouchableOpacity
          style={styles.whyRiskButton}
          onPress={() => navigate('understand-risk')}
          activeOpacity={0.8}>
          <Feather name="help-circle" size={18} color="#065F46" />
          <Text style={styles.whyRiskButtonText}>Why is this area at risk?</Text>
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
    paddingTop: 18,
    paddingBottom: 95,
  },
  locationHeader: {
    marginBottom: 20,
  },
  locationName: {
    fontSize: 24,
    fontWeight: '800',
    color: '#0F172A',
    letterSpacing: -0.3,
  },
  coordsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 6,
  },
  coordsText: {
    fontSize: 13,
    color: '#64748B',
  },
  updatedText: {
    fontSize: 12,
    color: '#94A3B8',
  },
  riskCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 20,
    borderWidth: 1.5,
    borderColor: '#FEE2E2',
    shadowColor: '#EF4444',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
    marginBottom: 20,
  },
  riskCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  highRiskPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  redDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#EF4444',
  },
  highRiskText: {
    fontSize: 12,
    fontWeight: '800',
    color: '#EF4444',
    letterSpacing: 0.5,
  },
  trendRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  trendText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#EF4444',
  },
  riskValuesRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 16,
    marginTop: 14,
  },
  percentageText: {
    fontSize: 48,
    fontWeight: '900',
    color: '#EF4444',
    lineHeight: 52,
  },
  labelsCol: {
    paddingBottom: 4,
  },
  probabilityLabel: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1E293B',
  },
  windowLabel: {
    fontSize: 13,
    color: '#64748B',
    marginTop: 2,
  },
  rangeTabsContainer: {
    flexDirection: 'row',
    backgroundColor: '#F1F5F9',
    borderRadius: 14,
    padding: 4,
    marginBottom: 24,
  },
  rangeTab: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 10,
  },
  rangeTabActive: {
    backgroundColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  rangeTabText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#64748B',
  },
  rangeTabTextActive: {
    color: '#0F172A',
    fontWeight: '700',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 14,
  },
  factorsList: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: '#F1F5F9',
    marginBottom: 24,
  },
  factorRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#F8FAFC',
  },
  factorLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  iconCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#E8F5E9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  factorLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#334155',
  },
  factorValue: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
  },
  whyRiskButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#ECFDF5',
    borderWidth: 1.5,
    borderColor: '#A7F3D0',
    borderRadius: 16,
    height: 52,
    gap: 8,
  },
  whyRiskButtonText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#065F46',
  },
});

