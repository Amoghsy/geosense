import { SafeAreaView } from 'react-native-safe-area-context';
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { Feather, Ionicons } from '@expo/vector-icons';
import { HeaderBar } from '@/components/HeaderBar';
import { useApp } from '@/context/AppContext';
import { geoSenseApi } from '@/services/api';

export function UnderstandRiskScreen() {
  const { navigate, selectedLocation, latestAssessmentId } = useApp();
  const [factors, setFactors] = useState<{ label: string; percentage: number }[]>([]);
  const [explanationText, setExplanationText] = useState<string>(
    'Analyzing environmental risk factors for this location...'
  );

  useEffect(() => {
    let active = true;
    const loadXai = async () => {
      try {
        let assId = latestAssessmentId;
        if (!assId) {
          const risk = await geoSenseApi.getCitizenRisk(
            selectedLocation.latitude,
            selectedLocation.longitude,
            selectedLocation.name
          );
          if (risk?.location_id) {
            const latest = await geoSenseApi.getLatestRisk(risk.location_id).catch(() => null);
            assId = latest?.assessment_id || null;
          }
        }
        if (!assId) return;
        const xai = await geoSenseApi.getRiskExplanation(assId);
        if (!active || !xai) return;

        const contribs = xai.factor_contributions || [];
        const total = contribs.reduce(
          (sum: number, c: any) => sum + Math.max(0, Number(c.weighted_contribution || c.raw_score || 0)),
          0
        );
        const mapped = contribs.map((c: any) => {
          const val = Math.max(0, Number(c.weighted_contribution || c.raw_score || 0));
          const pct = total > 0 ? Math.round((val / total) * 100) : Math.round(Number(c.raw_score || 0));
          return {
            label: String(c.factor || c.name || 'Factor').replace(/_/g, ' '),
            percentage: Math.min(100, Math.max(0, pct)),
          };
        });
        setFactors(mapped);
        if (xai.explanation_text) {
          setExplanationText(xai.explanation_text);
        }
      } catch {
        if (active) {
          setExplanationText('Unable to load detailed XAI breakdown from backend.');
        }
      }
    };
    loadXai();
    return () => {
      active = false;
    };
  }, [latestAssessmentId, selectedLocation.latitude, selectedLocation.longitude, selectedLocation.name]);

  const actions = [
    'Avoid travelling through unstable slopes',
    'Stay away from landslide-prone roads',
    'Prepare for possible evacuation',
    'Follow official disaster-management advisories',
  ];

  return (
    <SafeAreaView style={styles.safeArea} edges={['left', 'right']}>
      <HeaderBar
        title="Understand your risk"
        subtitle={`${selectedLocation.name} · XAI Breakdown`}
        variant="sub-light"
      />

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}>
        
        {/* Why is this area at risk card */}
        <View style={styles.analysisCard}>
          <View style={styles.analysisHeader}>
            <Ionicons name="sparkles" size={18} color="#00875A" />
            <Text style={styles.analysisTitle}>Why is this area at risk?</Text>
          </View>

          {/* Progress bars list */}
          <View style={styles.barsContainer}>
            {factors.length === 0 ? (
              <Text style={{ color: '#64748B', fontSize: 13 }}>
                Loading explainable AI factor contributions...
              </Text>
            ) : (
              factors.map((f, i) => (
                <View key={i} style={styles.barItem}>
                  <View style={styles.barLabelsRow}>
                    <Text style={styles.barLabel}>{f.label}</Text>
                    <Text style={styles.barPercentage}>{f.percentage}%</Text>
                  </View>
                  <View style={styles.progressBarTrack}>
                    <View
                      style={[
                        styles.progressBarFill,
                        { width: `${f.percentage}%` },
                      ]}
                    />
                  </View>
                </View>
              ))
            )}
          </View>

          {/* Explanation Callout */}
          <View style={styles.explanationBox}>
            <Text style={styles.explanationText}>{explanationText}</Text>
          </View>
        </View>

        {/* Recommended actions */}
        <Text style={styles.sectionTitle}>Recommended actions</Text>

        <View style={styles.actionsList}>
          {actions.map((act, i) => (
            <View key={i} style={styles.actionItem}>
              <View style={styles.shieldCircle}>
                <Feather name="shield" size={16} color="#00875A" />
              </View>
              <Text style={styles.actionItemText}>{act}</Text>
            </View>
          ))}
        </View>

        {/* View evacuation guidance button */}
        <TouchableOpacity
          style={styles.evacButton}
          onPress={() => navigate('evacuation')}
          activeOpacity={0.85}>
          <Feather name="navigation" size={18} color="#FFFFFF" />
          <Text style={styles.evacButtonText}>View evacuation guidance</Text>
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
  analysisCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
    borderColor: '#F1F5F9',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
    elevation: 2,
    marginBottom: 24,
  },
  analysisHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 18,
  },
  analysisTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#0F172A',
  },
  barsContainer: {
    gap: 14,
    marginBottom: 20,
  },
  barItem: {
    gap: 6,
  },
  barLabelsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  barLabel: {
    fontSize: 13,
    fontWeight: '500',
    color: '#334155',
  },
  barPercentage: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0F172A',
  },
  progressBarTrack: {
    height: 8,
    backgroundColor: '#F1F5F9',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: '#00875A',
    borderRadius: 4,
  },
  explanationBox: {
    backgroundColor: '#F8FAFC',
    borderRadius: 14,
    padding: 14,
    borderLeftWidth: 4,
    borderLeftColor: '#00875A',
  },
  explanationText: {
    fontSize: 13,
    color: '#475569',
    lineHeight: 19,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 14,
  },
  actionsList: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: '#F1F5F9',
    marginBottom: 24,
  },
  actionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F8FAFC',
  },
  shieldCircle: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#E8F5E9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionItemText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#1E293B',
    flex: 1,
  },
  evacButton: {
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
    shadowRadius: 10,
    elevation: 3,
  },
  evacButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
});
