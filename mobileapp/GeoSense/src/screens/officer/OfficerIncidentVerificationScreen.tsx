import { SafeAreaView } from 'react-native-safe-area-context';
import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  Alert,
} from 'react-native';
import { Feather, Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { HeaderBar } from '@/components/HeaderBar';
import { useApp } from '@/context/AppContext';

export function OfficerIncidentVerificationScreen() {
  const { verificationReports, verifyReport, rejectReport } = useApp();

  const handleVerify = (id: string) => {
    verifyReport(id);
    Alert.alert('Report Verified', 'This report has been verified and added to the live district alerts.');
  };

  const handleReject = (id: string) => {
    rejectReport(id);
    Alert.alert('Report Rejected', 'Citizen submission marked as unverified.');
  };

  const pendingCount = verificationReports.filter((r) => r.status === 'pending').length;

  return (
    <SafeAreaView style={styles.safeArea} edges={['left', 'right']}>
      <HeaderBar
        title="Incident Verification"
        subtitle="EAST KHASI HILLS"
        variant="officer-dark"
        rightAction={
          <TouchableOpacity hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
            <Feather name="filter" size={20} color="#FFFFFF" />
          </TouchableOpacity>
        }
      />

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}>
        
        {/* Header Count Row */}
        <View style={styles.headerCountRow}>
          <View>
            <Text style={styles.sectionTitle}>Citizen reports</Text>
            <Text style={styles.sectionSubTitle}>
              {pendingCount} reports awaiting your review
            </Text>
          </View>
          <View style={styles.pendingCountPill}>
            <Text style={styles.pendingCountText}>Pending ({pendingCount})</Text>
          </View>
        </View>

        {/* Report Card 1 */}
        {verificationReports.length > 0 && (
          <View style={styles.reportCard}>
            <View style={styles.imageBox}>
              <Image
                source={require('@/assets/images/design/rockfall_incident.jpg')}
                style={styles.reportPhoto}
                resizeMode="cover"
              />
              <View style={styles.severityTag}>
                <Ionicons name="warning-outline" size={12} color="#DC2626" />
                <Text style={styles.severityTagText}>High severity</Text>
              </View>
              <View style={styles.photosCountBadge}>
                <Feather name="image" size={12} color="#FFFFFF" />
                <Text style={styles.photosCountText}>3 photos</Text>
              </View>
            </View>

            <View style={styles.reportContent}>
              <View style={styles.idTimeRow}>
                <Text style={styles.reportId}>{verificationReports[0].id}</Text>
                <Text style={styles.reportTime}>{verificationReports[0].timeAgo}</Text>
              </View>

              <Text style={styles.reportTitle}>{verificationReports[0].title}</Text>

              <View style={styles.reportLocationRow}>
                <Feather name="map-pin" size={14} color="#64748B" />
                <Text style={styles.reportLocationText}>
                  {verificationReports[0].location} • {verificationReports[0].distance}
                </Text>
              </View>

              <View style={styles.quoteBox}>
                <Text style={styles.quoteText}>{verificationReports[0].quote}</Text>
              </View>

              <View style={styles.submitterRow}>
                <Feather name="user" size={14} color="#64748B" />
                <Text style={styles.submitterText}>{verificationReports[0].submitter}</Text>
              </View>

              {/* Action Buttons: Reject and Verify */}
              {verificationReports[0].status === 'pending' ? (
                <View style={styles.cardActionsRow}>
                  <TouchableOpacity
                    style={styles.rejectBtn}
                    onPress={() => handleReject(verificationReports[0].id)}
                    activeOpacity={0.75}>
                    <Feather name="x" size={18} color="#EF4444" />
                    <Text style={styles.rejectBtnText}>Reject</Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={styles.verifyBtn}
                    onPress={() => handleVerify(verificationReports[0].id)}
                    activeOpacity={0.85}>
                    <Feather name="check" size={18} color="#FFFFFF" />
                    <Text style={styles.verifyBtnText}>Verify</Text>
                  </TouchableOpacity>
                </View>
              ) : (
                <View
                  style={[
                    styles.statusResultBox,
                    verificationReports[0].status === 'verified'
                      ? styles.verifiedResult
                      : styles.rejectedResult,
                  ]}>
                  <Feather
                    name={
                      verificationReports[0].status === 'verified'
                        ? 'check-circle'
                        : 'x-circle'
                    }
                    size={16}
                    color={
                      verificationReports[0].status === 'verified'
                        ? '#059669'
                        : '#DC2626'
                    }
                  />
                  <Text
                    style={[
                      styles.statusResultText,
                      {
                        color:
                          verificationReports[0].status === 'verified'
                            ? '#059669'
                            : '#DC2626',
                      },
                    ]}>
                    Report {verificationReports[0].status.toUpperCase()}
                  </Text>
                </View>
              )}
            </View>
          </View>
        )}

        {/* Report Card 2 (Compact / Moderate) */}
        {verificationReports.length > 1 && (
          <View style={styles.compactCard}>
            <Image
              source={require('@/assets/images/design/field_report_photo.jpg')}
              style={styles.compactThumb}
              resizeMode="cover"
            />
            <View style={styles.compactInfo}>
              <View style={styles.compactTopRow}>
                <Text style={styles.compactId}>{verificationReports[1].id}</Text>
                <View style={styles.moderatePill}>
                  <Text style={styles.moderatePillText}>Moderate</Text>
                </View>
              </View>

              <Text style={styles.compactTitle}>{verificationReports[1].title}</Text>
              <Text style={styles.compactSub}>Mawsynram • 28 min ago</Text>

              <View style={styles.compactFooterRow}>
                <Text style={styles.compactMeta}>2 photos • 6.4 km away</Text>
                <TouchableOpacity
                  onPress={() => handleVerify(verificationReports[1].id)}
                  style={styles.reviewLinkRow}>
                  <Text style={styles.reviewLinkText}>Review report</Text>
                  <Feather name="arrow-right" size={14} color="#00875A" />
                </TouchableOpacity>
              </View>
            </View>
          </View>
        )}

        {/* Verification Note */}
        <View style={styles.verificationNoteBox}>
          <Feather name="info" size={16} color="#64748B" />
          <Text style={styles.verificationNoteText}>
            Verify only after checking the evidence and location. Verified reports inform district alerts.
          </Text>
        </View>

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
    paddingBottom: 95,
  },
  headerCountRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#0F172A',
  },
  sectionSubTitle: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
  pendingCountPill: {
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  pendingCountText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#B45309',
  },
  reportCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 22,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
    elevation: 2,
  },
  imageBox: {
    height: 170,
    position: 'relative',
  },
  reportPhoto: {
    width: '100%',
    height: '100%',
  },
  severityTag: {
    position: 'absolute',
    top: 12,
    left: 12,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 4,
  },
  severityTagText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#DC2626',
  },
  photosCountBadge: {
    position: 'absolute',
    bottom: 12,
    right: 12,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(15, 23, 42, 0.75)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 5,
  },
  photosCountText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  reportContent: {
    padding: 18,
  },
  idTimeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  reportId: {
    fontSize: 12,
    fontWeight: '700',
    color: '#00875A',
  },
  reportTime: {
    fontSize: 12,
    color: '#64748B',
  },
  reportTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: '#0F172A',
    marginBottom: 6,
  },
  reportLocationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 12,
  },
  reportLocationText: {
    fontSize: 13,
    color: '#64748B',
  },
  quoteBox: {
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    padding: 12,
    borderLeftWidth: 3,
    borderLeftColor: '#CBD5E1',
    marginBottom: 12,
  },
  quoteText: {
    fontSize: 13,
    color: '#334155',
    fontStyle: 'italic',
    lineHeight: 18,
  },
  submitterRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 16,
  },
  submitterText: {
    fontSize: 12,
    color: '#64748B',
  },
  cardActionsRow: {
    flexDirection: 'row',
    gap: 12,
  },
  rejectBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FEE2E2',
    borderRadius: 14,
    height: 46,
    gap: 6,
  },
  rejectBtnText: {
    color: '#EF4444',
    fontSize: 14,
    fontWeight: '700',
  },
  verifyBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#00875A',
    borderRadius: 14,
    height: 46,
    gap: 6,
  },
  verifyBtnText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  statusResultBox: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderRadius: 12,
    gap: 8,
  },
  verifiedResult: {
    backgroundColor: '#D1FAE5',
  },
  rejectedResult: {
    backgroundColor: '#FEE2E2',
  },
  statusResultText: {
    fontSize: 13,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  compactCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 14,
    flexDirection: 'row',
    gap: 14,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 20,
  },
  compactThumb: {
    width: 76,
    height: 76,
    borderRadius: 12,
  },
  compactInfo: {
    flex: 1,
  },
  compactTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  compactId: {
    fontSize: 11,
    fontWeight: '700',
    color: '#64748B',
  },
  moderatePill: {
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  moderatePillText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#B45309',
  },
  compactTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
    marginTop: 2,
  },
  compactSub: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 1,
  },
  compactFooterRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
  },
  compactMeta: {
    fontSize: 11,
    color: '#94A3B8',
  },
  reviewLinkRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  reviewLinkText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#00875A',
  },
  verificationNoteBox: {
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: 6,
    marginTop: 4,
  },
  verificationNoteText: {
    fontSize: 11,
    color: '#64748B',
    lineHeight: 16,
    flex: 1,
  },
});

