import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  ScrollView,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { HeaderBar } from '@/components/HeaderBar';
import { useApp } from '@/context/AppContext';

export function ReportIncidentSuccessScreen() {
  const { navigate, resetIncidentDraft, incidentDraft } = useApp();

  const handleBackHome = () => {
    resetIncidentDraft();
    navigate('citizen-home');
  };

  const handleReportAnother = () => {
    resetIncidentDraft();
    navigate('report-incident-1');
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <HeaderBar title="Report submitted" variant="sub-light" />

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}>
        
        {/* Large Checkmark Badge */}
        <View style={styles.successIconCircle}>
          <Feather name="check" size={40} color="#FFFFFF" />
        </View>

        {/* Heading & Subtitle */}
        <Text style={styles.headingTitle}>
          Thank you for looking out{'\n'}for your community.
        </Text>
        <Text style={styles.subHeading}>
          Your incident report has been submitted successfully.
        </Text>

        {/* Receipt / Details Box */}
        <View style={styles.receiptCard}>
          <View style={styles.receiptRow}>
            <Text style={styles.receiptLabel}>Reference ID</Text>
            <Text style={styles.receiptValue}>{incidentDraft.referenceId || 'GS-2026-01482'}</Text>
          </View>
          <View style={styles.receiptDivider} />

          <View style={styles.receiptRow}>
            <Text style={styles.receiptLabel}>Incident</Text>
            <Text style={styles.receiptValue}>{incidentDraft.type}</Text>
          </View>
          <View style={styles.receiptDivider} />

          <View style={styles.receiptRow}>
            <Text style={styles.receiptLabel}>Location</Text>
            <Text style={styles.receiptValue}>{incidentDraft.location}</Text>
          </View>
          <View style={styles.receiptDivider} />

          <View style={styles.receiptRow}>
            <Text style={styles.receiptLabel}>Status</Text>
            <View style={styles.statusPill}>
              <View style={styles.greenDot} />
              <Text style={styles.statusText}>Submitted · Awaiting review</Text>
            </View>
          </View>
        </View>

        {/* Notice text */}
        <Text style={styles.disclaimerNotice}>
          This is a reporting confirmation, not an emergency dispatch. For urgent assistance, call 112.
        </Text>

        {/* Action Buttons */}
        <TouchableOpacity
          style={styles.backHomeBtn}
          onPress={handleBackHome}
          activeOpacity={0.85}>
          <Feather name="home" size={18} color="#FFFFFF" />
          <Text style={styles.backHomeText}>Back to Home</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.reportAnotherBtn}
          onPress={handleReportAnother}
          activeOpacity={0.75}>
          <Text style={styles.reportAnotherText}>Report another incident</Text>
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
    paddingHorizontal: 24,
    paddingTop: 36,
    paddingBottom: 40,
    alignItems: 'center',
  },
  successIconCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#00875A',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
    shadowColor: '#00875A',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 4,
  },
  headingTitle: {
    fontSize: 24,
    fontWeight: '800',
    color: '#0F172A',
    textAlign: 'center',
    lineHeight: 32,
    marginBottom: 10,
  },
  subHeading: {
    fontSize: 14,
    color: '#64748B',
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 28,
  },
  receiptCard: {
    width: '100%',
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 20,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
  },
  receiptRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
  },
  receiptLabel: {
    fontSize: 14,
    color: '#64748B',
    fontWeight: '500',
  },
  receiptValue: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
  },
  receiptDivider: {
    height: 1,
    backgroundColor: '#F1F5F9',
    marginVertical: 4,
  },
  statusPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  greenDot: {
    width: 7,
    height: 7,
    borderRadius: 3.5,
    backgroundColor: '#10B981',
  },
  statusText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#00875A',
  },
  disclaimerNotice: {
    fontSize: 12,
    color: '#94A3B8',
    textAlign: 'center',
    lineHeight: 18,
    marginBottom: 32,
    paddingHorizontal: 10,
  },
  backHomeBtn: {
    width: '100%',
    height: 52,
    borderRadius: 16,
    backgroundColor: '#00875A',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginBottom: 12,
    shadowColor: '#00875A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 3,
  },
  backHomeText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  reportAnotherBtn: {
    width: '100%',
    height: 50,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  reportAnotherText: {
    color: '#334155',
    fontSize: 15,
    fontWeight: '600',
  },
});

