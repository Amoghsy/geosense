import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  TextInput,
} from 'react-native';
import { Feather, Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { HeaderBar } from '@/components/HeaderBar';
import { useApp } from '@/context/AppContext';

export function ReportIncidentStep2Screen() {
  const { navigate, incidentDraft, updateIncidentDraft } = useApp();
  const [severity, setSeverity] = useState<'Low' | 'Moderate' | 'High' | 'Critical'>('High');
  const [roadAccessibility, setRoadAccessibility] = useState('Partially blocked');
  const [peopleAffected, setPeopleAffected] = useState('Not known');

  const severities: ('Low' | 'Moderate' | 'High' | 'Critical')[] = [
    'Low',
    'Moderate',
    'High',
    'Critical',
  ];

  const handleSubmit = () => {
    updateIncidentDraft({
      severity,
      accessibility: roadAccessibility,
      peopleAffected,
    });
    navigate('report-incident-success');
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <HeaderBar
        title="Incident details"
        subtitle="Step 2 of 2 · Review & submit"
        variant="sub-light"
      />

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}>
        
        {/* Summary Card */}
        <View style={styles.summaryCard}>
          <Text style={styles.summaryTitle}>
            {incidentDraft.type} · {incidentDraft.location}
          </Text>
          <Text style={styles.summaryDesc}>
            1 photo attached · GPS location confirmed {incidentDraft.coords}
          </Text>
        </View>

        {/* Incident Time */}
        <Text style={styles.fieldLabel}>Incident time</Text>
        <View style={styles.inputWithIcon}>
          <Text style={styles.inputValue}>07 Nov 2026 · 09:35 AM</Text>
          <Feather name="calendar" size={18} color="#64748B" />
        </View>

        {/* Severity selection */}
        <Text style={styles.fieldLabel}>Severity *</Text>
        <View style={styles.severityRow}>
          {severities.map((s) => {
            const isSelected = severity === s;
            return (
              <TouchableOpacity
                key={s}
                style={[
                  styles.severityPill,
                  isSelected && styles.severityPillActive,
                ]}
                onPress={() => setSeverity(s)}>
                <Text
                  style={[
                    styles.severityPillText,
                    isSelected && styles.severityPillTextActive,
                  ]}>
                  {s}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>

        {/* Road Accessibility */}
        <Text style={styles.fieldLabel}>Road accessibility</Text>
        <TouchableOpacity style={styles.inputWithIcon} activeOpacity={0.8}>
          <Text style={styles.inputValue}>{roadAccessibility}</Text>
          <Feather name="chevron-down" size={18} color="#64748B" />
        </TouchableOpacity>

        {/* People affected (optional) */}
        <Text style={styles.fieldLabel}>People affected (optional)</Text>
        <View style={styles.inputWithIcon}>
          <TextInput
            style={styles.textInputFlex}
            value={peopleAffected}
            onChangeText={setPeopleAffected}
            placeholder="e.g. Not known, 2 people, etc."
            placeholderTextColor="#94A3B8"
          />
          <Feather name="users" size={18} color="#64748B" />
        </View>

        {/* Info Disclaimer Card */}
        <View style={styles.infoCard}>
          <View style={styles.infoHeaderRow}>
            <Feather name="info" size={16} color="#00875A" />
            <Text style={styles.infoTitle}>Your report helps the community</Text>
          </View>
          <Text style={styles.infoText}>
            Reports are reviewed before they inform public advisories. Submitting a report does not dispatch emergency services.
          </Text>
          <Text style={styles.emergencyPrompt}>
            Immediate assistance? <Text style={styles.emergencyLink}>Call 112.</Text>
          </Text>
        </View>

        {/* Submit Incident Report Button */}
        <TouchableOpacity
          style={styles.submitButton}
          onPress={handleSubmit}
          activeOpacity={0.85}>
          <Feather name="send" size={18} color="#FFFFFF" />
          <Text style={styles.submitButtonText}>Submit Incident Report</Text>
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
    paddingBottom: 40,
  },
  summaryCard: {
    backgroundColor: '#ECFDF5',
    borderWidth: 1,
    borderColor: '#A7F3D0',
    borderRadius: 16,
    padding: 16,
    marginBottom: 20,
  },
  summaryTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#065F46',
  },
  summaryDesc: {
    fontSize: 12,
    color: '#047857',
    marginTop: 4,
    lineHeight: 18,
  },
  fieldLabel: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 8,
    marginTop: 6,
  },
  inputWithIcon: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 14,
    height: 50,
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  inputValue: {
    fontSize: 14,
    color: '#0F172A',
    fontWeight: '500',
  },
  textInputFlex: {
    flex: 1,
    fontSize: 14,
    color: '#0F172A',
  },
  severityRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 16,
  },
  severityPill: {
    flex: 1,
    height: 44,
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    alignItems: 'center',
    justifyContent: 'center',
  },
  severityPillActive: {
    borderColor: '#EF4444',
    borderWidth: 1.5,
    backgroundColor: '#FEF2F2',
  },
  severityPillText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#64748B',
  },
  severityPillTextActive: {
    color: '#EF4444',
    fontWeight: '700',
  },
  infoCard: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 16,
    padding: 16,
    marginTop: 10,
    marginBottom: 24,
  },
  infoHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 6,
  },
  infoTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
  },
  infoText: {
    fontSize: 12,
    color: '#64748B',
    lineHeight: 18,
  },
  emergencyPrompt: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 8,
  },
  emergencyLink: {
    color: '#EF4444',
    fontWeight: '700',
  },
  submitButton: {
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
  submitButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
});

