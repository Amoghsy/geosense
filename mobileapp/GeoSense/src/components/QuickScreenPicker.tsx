import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Modal,
  ScrollView,
  SafeAreaView,
} from 'react-native';
import { Feather, Ionicons } from '@expo/vector-icons';
import { useApp, ScreenName } from '@/context/AppContext';

export function QuickScreenPicker() {
  const [isOpen, setIsOpen] = useState(false);
  const { currentScreen, navigate, role, setRole } = useApp();

  const citizenScreens: { name: ScreenName; label: string; page: string }[] = [
    { name: 'citizen-home', label: '1. Citizen Home Dashboard', page: 'PDF 1 • Page 1' },
    { name: 'safety-outlook', label: '2. Your Safety Outlook', page: 'PDF 1 • Page 1 (Right)' },
    { name: 'map', label: '3. Live Risk Map', page: 'PDF 1 • Page 2' },
    { name: 'location-details', label: '4. Location Risk Details', page: 'PDF 1 • Page 2' },
    { name: 'understand-risk', label: '5. Understand Your Risk', page: 'PDF 1 • Page 2' },
    { name: 'evacuation', label: '6. Evacuation Guidance', page: 'PDF 1 • Page 3' },
    { name: 'ar-view', label: '7. AR Field Intelligence', page: 'PDF 1 • Page 4' },
    { name: 'resources', label: '8. Nearby Resources', page: 'PDF 1 • Page 5' },
    { name: 'report-incident-1', label: '9. Report Incident (Step 1)', page: 'PDF 1 • Page 6' },
    { name: 'report-incident-2', label: '10. Incident Details (Step 2)', page: 'PDF 1 • Page 6' },
    { name: 'report-incident-success', label: '11. Report Submitted Confirmation', page: 'PDF 1 • Page 6' },
    { name: 'alerts', label: '12. Alerts & Notifications', page: 'PDF 1 • Page 7' },
    { name: 'profile', label: '13. Profile & Settings', page: 'PDF 1 • Page 8' },
    { name: 'offline-maps', label: '14. Offline Maps Readiness', page: 'PDF 1 • Page 8' },
  ];

  const officerScreens: { name: ScreenName; label: string; page: string }[] = [
    { name: 'officer-login', label: '1. Field Officer Login', page: 'PDF 2 • Page 1' },
    { name: 'officer-home', label: '2. Field Officer Dashboard', page: 'PDF 2 • Page 5' },
    { name: 'officer-mission', label: '3. Assigned Mission (GS-2048)', page: 'PDF 2 • Page 4' },
    { name: 'officer-ar', label: '4. AR Field Inspection', page: 'PDF 2 • Page 3' },
    { name: 'officer-verification', label: '5. Incident Verification', page: 'PDF 2 • Page 6' },
    { name: 'officer-report', label: '6. New Field Report', page: 'PDF 2 • Page 7' },
    { name: 'officer-alerts', label: '7. Field Officer Alerts', page: 'PDF 2 • Page 2' },
    { name: 'officer-offline', label: '8. Field Officer Offline Mode', page: 'PDF 2 • Page 9' },
    { name: 'officer-profile', label: '9. Field Officer Profile', page: 'PDF 2 • Page 8' },
  ];

  const handleSelect = (name: ScreenName) => {
    navigate(name);
    setIsOpen(false);
  };

  return (
    <>
      {/* Floating Pill on bottom left of screen */}
      <TouchableOpacity
        style={styles.floatingTrigger}
        onPress={() => setIsOpen(true)}
        activeOpacity={0.85}>
        <Feather name="layers" size={14} color="#FFFFFF" />
        <Text style={styles.floatingTriggerText}>All Screens</Text>
      </TouchableOpacity>

      {/* Screen Switcher Modal */}
      <Modal
        visible={isOpen}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setIsOpen(false)}>
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <View>
              <Text style={styles.modalTitle}>GeoSense Screen Index</Text>
              <Text style={styles.modalSubtitle}>All 23 screens from both UX PDFs</Text>
            </View>
            <TouchableOpacity onPress={() => setIsOpen(false)} style={styles.closeBtn}>
              <Feather name="x" size={20} color="#0F172A" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalBody} showsVerticalScrollIndicator={false}>
            {/* Citizen Section */}
            <View style={styles.sectionHeader}>
              <View style={[styles.sectionDot, { backgroundColor: '#00875A' }]} />
              <Text style={styles.sectionHeaderText}>Citizen App Screens (PDF 1)</Text>
            </View>

            <View style={styles.screensList}>
              {citizenScreens.map((item) => {
                const isActive = currentScreen === item.name;
                return (
                  <TouchableOpacity
                    key={item.name}
                    style={[styles.screenItem, isActive && styles.screenItemActive]}
                    onPress={() => handleSelect(item.name)}>
                    <View style={styles.itemLeft}>
                      <Text style={[styles.itemLabel, isActive && styles.itemLabelActive]}>
                        {item.label}
                      </Text>
                      <Text style={styles.itemPage}>{item.page}</Text>
                    </View>
                    {isActive && <Feather name="check" size={18} color="#00875A" />}
                  </TouchableOpacity>
                );
              })}
            </View>

            {/* Officer Section */}
            <View style={[styles.sectionHeader, { marginTop: 24 }]}>
              <View style={[styles.sectionDot, { backgroundColor: '#0D5C3A' }]} />
              <Text style={styles.sectionHeaderText}>Field Officer App Screens (PDF 2)</Text>
            </View>

            <View style={styles.screensList}>
              {officerScreens.map((item) => {
                const isActive = currentScreen === item.name;
                return (
                  <TouchableOpacity
                    key={item.name}
                    style={[styles.screenItem, isActive && styles.screenItemActive]}
                    onPress={() => handleSelect(item.name)}>
                    <View style={styles.itemLeft}>
                      <Text style={[styles.itemLabel, isActive && styles.itemLabelActive]}>
                        {item.label}
                      </Text>
                      <Text style={styles.itemPage}>{item.page}</Text>
                    </View>
                    {isActive && <Feather name="check" size={18} color="#00875A" />}
                  </TouchableOpacity>
                );
              })}
            </View>

            <View style={{ height: 40 }} />
          </ScrollView>
        </SafeAreaView>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  floatingTrigger: {
    position: 'absolute',
    bottom: 80,
    left: 16,
    zIndex: 9999,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(15, 23, 42, 0.88)',
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 20,
    gap: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.25,
    shadowRadius: 6,
    elevation: 6,
  },
  floatingTriggerText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#0F172A',
  },
  modalSubtitle: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
  closeBtn: {
    padding: 8,
    borderRadius: 20,
    backgroundColor: '#F1F5F9',
  },
  modalBody: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 10,
  },
  sectionDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  sectionHeaderText: {
    fontSize: 14,
    fontWeight: '800',
    color: '#0F172A',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  screensList: {
    backgroundColor: '#F8FAFC',
    borderRadius: 16,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  screenItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  screenItemActive: {
    backgroundColor: '#ECFDF5',
  },
  itemLeft: {
    flex: 1,
  },
  itemLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1E293B',
  },
  itemLabelActive: {
    color: '#00875A',
    fontWeight: '800',
  },
  itemPage: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 2,
  },
});

