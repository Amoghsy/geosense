import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  Switch,
} from 'react-native';
import { Feather, Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { HeaderBar } from '@/components/HeaderBar';
import { useApp } from '@/context/AppContext';

export function OfficerProfileScreen() {
  const { logoutOfficer, navigate } = useApp();
  const [criticalAlertsEnabled, setCriticalAlertsEnabled] = useState(true);

  return (
    <SafeAreaView style={styles.safeArea}>
      <HeaderBar
        title="Profile"
        variant="officer-dark"
        rightAction={
          <TouchableOpacity hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
            <Feather name="edit-2" size={20} color="#FFFFFF" />
          </TouchableOpacity>
        }
      />

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}>
        
        {/* Officer Card */}
        <View style={styles.officerCard}>
          <View style={styles.cardHeaderRow}>
            <View style={styles.avatarCircle}>
              <Text style={styles.avatarText}>RK</Text>
            </View>

            <View style={styles.nameCol}>
              <Text style={styles.officerName}>Riban Khongwir</Text>
              <Text style={styles.officerRole}>Field Officer · FO-1027</Text>
              <View style={styles.onDutyPill}>
                <View style={styles.onDutyDot} />
                <Text style={styles.onDutyText}>On Duty</Text>
              </View>
            </View>
          </View>

          <View style={styles.districtDivider} />

          <View style={styles.districtRow}>
            <View style={styles.districtLeft}>
              <Ionicons name="location-outline" size={18} color="#00875A" />
              <View>
                <Text style={styles.districtLabel}>ASSIGNED DISTRICT</Text>
                <Text style={styles.districtValue}>East Khasi Hills, Meghalaya</Text>
              </View>
            </View>
            <Ionicons name="checkmark-circle" size={20} color="#00875A" />
          </View>
        </View>

        {/* 3 Metrics Cards */}
        <View style={styles.metricsRow}>
          <View style={styles.metricCard}>
            <Text style={styles.metricBigNum}>48</Text>
            <Text style={styles.metricLabel}>Missions done</Text>
          </View>

          <View style={styles.metricCard}>
            <Text style={styles.metricBigNum}>126</Text>
            <Text style={styles.metricLabel}>Reports filed</Text>
          </View>

          <View style={styles.metricCard}>
            <Text style={styles.metricBigNum}>18</Text>
            <Text style={styles.metricLabel}>Verified alerts</Text>
          </View>
        </View>

        {/* Mission History Section */}
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionTitle}>Mission history</Text>
          <TouchableOpacity>
            <Text style={styles.viewAllText}>View all</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.historyCard}>
          <TouchableOpacity style={styles.historyItem} activeOpacity={0.7}>
            <View style={styles.checkIconBox}>
              <Feather name="check" size={16} color="#00875A" />
            </View>
            <View style={styles.historyInfo}>
              <Text style={styles.historyTitle}>Nongriat trail · Z3</Text>
              <Text style={styles.historySub}>Risk assessment • 16 Jun</Text>
            </View>
            <Feather name="chevron-right" size={18} color="#94A3B8" />
          </TouchableOpacity>

          <View style={styles.historyDivider} />

          <TouchableOpacity style={styles.historyItem} activeOpacity={0.7}>
            <View style={styles.checkIconBox}>
              <Feather name="check" size={16} color="#00875A" />
            </View>
            <View style={styles.historyInfo}>
              <Text style={styles.historyTitle}>Mawkdok slope · S4</Text>
              <Text style={styles.historySub}>Site inspection • 15 Jun</Text>
            </View>
            <Feather name="chevron-right" size={18} color="#94A3B8" />
          </TouchableOpacity>
        </View>

        {/* Settings Group */}
        <View style={styles.settingsGroup}>
          {/* Alert Settings */}
          <View style={styles.settingRow}>
            <View style={styles.settingIconBox}>
              <Ionicons name="notifications-outline" size={20} color="#0F172A" />
            </View>
            <View style={styles.settingInfo}>
              <Text style={styles.settingTitle}>Alert settings</Text>
              <Text style={styles.settingSub}>Critical alerts always enabled</Text>
            </View>
            <Switch
              value={criticalAlertsEnabled}
              onValueChange={setCriticalAlertsEnabled}
              trackColor={{ false: '#CBD5E1', true: '#00875A' }}
              thumbColor="#FFFFFF"
            />
          </View>

          <View style={styles.historyDivider} />

          {/* Offline Storage */}
          <TouchableOpacity
            style={styles.settingRow}
            onPress={() => navigate('officer-offline')}
            activeOpacity={0.7}>
            <View style={styles.settingIconBox}>
              <Feather name="hard-drive" size={20} color="#0F172A" />
            </View>
            <View style={styles.settingInfo}>
              <Text style={styles.settingTitle}>Offline storage</Text>
              <Text style={styles.settingSub}>286 MB used • 12 cached locations</Text>
            </View>
            <Feather name="chevron-right" size={18} color="#94A3B8" />
          </TouchableOpacity>
        </View>

        {/* Log Out Button */}
        <TouchableOpacity
          style={styles.logoutBtn}
          onPress={logoutOfficer}
          activeOpacity={0.8}>
          <Feather name="log-out" size={18} color="#0F172A" />
          <Text style={styles.logoutBtnText}>Log out</Text>
        </TouchableOpacity>

        <Text style={styles.versionFooter}>
          GeoSense Field Officer • Version 2.4.0
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
  officerCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 22,
    padding: 18,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
    elevation: 2,
  },
  cardHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
  },
  avatarCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#D1FAE5',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: '#A7F3D0',
  },
  avatarText: {
    fontSize: 22,
    fontWeight: '900',
    color: '#065F46',
  },
  nameCol: {
    flex: 1,
  },
  officerName: {
    fontSize: 20,
    fontWeight: '800',
    color: '#0F172A',
  },
  officerRole: {
    fontSize: 13,
    color: '#64748B',
    marginTop: 2,
  },
  onDutyPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#D1FAE5',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
    gap: 4,
    alignSelf: 'flex-start',
    marginTop: 6,
  },
  onDutyDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#10B981',
  },
  onDutyText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#065F46',
  },
  districtDivider: {
    height: 1,
    backgroundColor: '#F1F5F9',
    marginVertical: 14,
  },
  districtRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  districtLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  districtLabel: {
    fontSize: 10,
    fontWeight: '800',
    color: '#64748B',
    letterSpacing: 0.8,
  },
  districtValue: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
    marginTop: 1,
  },
  metricsRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 22,
  },
  metricCard: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    paddingVertical: 18,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  metricBigNum: {
    fontSize: 26,
    fontWeight: '900',
    color: '#0F172A',
  },
  metricLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: '#64748B',
    marginTop: 4,
    textAlign: 'center',
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#0F172A',
  },
  viewAllText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#00875A',
  },
  historyCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 20,
  },
  historyItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    gap: 12,
  },
  checkIconBox: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#D1FAE5',
    alignItems: 'center',
    justifyContent: 'center',
  },
  historyInfo: {
    flex: 1,
  },
  historyTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
  },
  historySub: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 2,
  },
  historyDivider: {
    height: 1,
    backgroundColor: '#F8FAFC',
  },
  settingsGroup: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 20,
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    gap: 12,
  },
  settingIconBox: {
    width: 36,
    height: 36,
    borderRadius: 12,
    backgroundColor: '#F1F5F9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  settingInfo: {
    flex: 1,
  },
  settingTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
  },
  settingSub: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 2,
  },
  logoutBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    height: 50,
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
    gap: 8,
    marginBottom: 16,
  },
  logoutBtnText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
  },
  versionFooter: {
    textAlign: 'center',
    fontSize: 11,
    color: '#94A3B8',
  },
});

