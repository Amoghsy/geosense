import { SafeAreaView } from 'react-native-safe-area-context';
import React from 'react';
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

export function OfficerARInspectionScreen() {
  const { navigate } = useApp();

  const handleCapture = () => {
    Alert.alert('Evidence Captured', 'Photo with GPS and telemetry metadata tagged.', [
      { text: 'Attach to New Report', onPress: () => navigate('officer-report') },
      { text: 'Cancel', style: 'cancel' },
    ]);
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['left', 'right']}>
      <HeaderBar
        title="AR Field Inspection"
        subtitle="SOHRA SLOPE · S1"
        variant="officer-dark"
        rightAction={
          <TouchableOpacity hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
            <Feather name="maximize-2" size={20} color="#FFFFFF" />
          </TouchableOpacity>
        }
      />

      <View style={styles.container}>
        <Image
          source={require('@/assets/images/design/officer_ar_view.jpg')}
          style={StyleSheet.absoluteFill}
          resizeMode="cover"
        />
          
          {/* Top HUD Indicators */}
          <View style={styles.topHudRow}>
            <View style={styles.liveBadge}>
              <View style={styles.greenLiveDot} />
              <Text style={styles.liveBadgeText}>LIVE CAMERA</Text>
            </View>

            <View style={styles.aiBadge}>
              <Feather name="cpu" size={14} color="#065F46" />
              <Text style={styles.aiBadgeText}>AI confidence 96%</Text>
            </View>
          </View>

          {/* AR Detection 1: High Risk Unstable Slope with Reticle */}
          <View style={styles.highRiskBox}>
            <View style={styles.highRiskTag}>
              <Ionicons name="warning" size={14} color="#FFFFFF" />
              <View>
                <Text style={styles.tagTitle}>HIGH RISK</Text>
                <Text style={styles.tagDesc}>Unstable slope • 18 m</Text>
              </View>
            </View>
            
            {/* Center Reticle Brackets */}
            <View style={styles.reticleCorners}>
              <View style={[styles.corner, styles.cornerTL]} />
              <View style={[styles.corner, styles.cornerTR]} />
              <View style={[styles.corner, styles.cornerBL]} />
              <View style={[styles.corner, styles.cornerBR]} />
            </View>
          </View>

          {/* AR Detection 2: Moderate Loose Debris */}
          <View style={styles.moderateBox}>
            <View style={styles.moderateTag}>
              <Ionicons name="warning" size={14} color="#FFFFFF" />
              <Text style={styles.moderateTagText}>Moderate • Loose debris</Text>
            </View>
          </View>

          {/* AR Detection 3: Safe Observation Point */}
          <View style={styles.safeBox}>
            <View style={styles.safeTag}>
              <Feather name="shield" size={14} color="#FFFFFF" />
              <Text style={styles.safeTagText}>Safe observation point</Text>
            </View>
          </View>

          {/* Bottom Telemetry HUD Bar */}
          <View style={styles.telemetryOverlay}>
            <View style={styles.telemetryHeader}>
              <View style={styles.coordsCol}>
                <View style={styles.coordsMainRow}>
                  <Feather name="crosshair" size={14} color="#10B981" />
                  <Text style={styles.coordsMainText}>25.2700° N, 91.7300° E</Text>
                </View>
                <Text style={styles.telemetrySubText}>
                  GPS ±4 m • Facing NE 048° • 1,350 m
                </Text>
              </View>
              <Feather name="compass" size={24} color="#FFFFFF" />
            </View>

            {/* Capture Evidence Button */}
            <TouchableOpacity
              style={styles.captureBtn}
              onPress={handleCapture}
              activeOpacity={0.85}>
              <Feather name="camera" size={20} color="#FFFFFF" />
              <Text style={styles.captureBtnText}>Capture Evidence</Text>
            </TouchableOpacity>

            <Text style={styles.safetyGuidanceText}>
              AI-assisted view. Confirm conditions on site.{'\n'}Do not enter marked risk zones.
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
    backgroundColor: '#000000',
  },
  bgImage: {
    flex: 1,
    justifyContent: 'space-between',
  },
  topHudRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 16,
  },
  liveBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(15, 23, 42, 0.75)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    gap: 6,
  },
  greenLiveDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#10B981',
  },
  liveBadgeText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  aiBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#D1FAE5',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    gap: 6,
  },
  aiBadgeText: {
    color: '#065F46',
    fontSize: 12,
    fontWeight: '800',
  },
  highRiskBox: {
    position: 'absolute',
    top: '26%',
    right: '8%',
    width: '54%',
    height: '32%',
    borderWidth: 2,
    borderColor: '#EF4444',
    backgroundColor: 'rgba(239, 68, 68, 0.22)',
    borderRadius: 16,
    justifyContent: 'space-between',
    padding: 8,
  },
  highRiskTag: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#DC2626',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 10,
    gap: 6,
    alignSelf: 'flex-start',
  },
  tagTitle: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '900',
  },
  tagDesc: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '500',
  },
  reticleCorners: {
    alignSelf: 'center',
    width: 44,
    height: 44,
    position: 'relative',
    marginBottom: 20,
  },
  corner: {
    position: 'absolute',
    width: 12,
    height: 12,
    borderColor: '#FFFFFF',
  },
  cornerTL: { top: 0, left: 0, borderTopWidth: 2, borderLeftWidth: 2 },
  cornerTR: { top: 0, right: 0, borderTopWidth: 2, borderRightWidth: 2 },
  cornerBL: { bottom: 0, left: 0, borderBottomWidth: 2, borderLeftWidth: 2 },
  cornerBR: { bottom: 0, right: 0, borderBottomWidth: 2, borderRightWidth: 2 },
  moderateBox: {
    position: 'absolute',
    top: '46%',
    left: '8%',
    width: '38%',
    height: '18%',
    borderWidth: 2,
    borderColor: '#F59E0B',
    backgroundColor: 'rgba(245, 158, 11, 0.22)',
    borderRadius: 14,
    padding: 6,
  },
  moderateTag: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#D97706',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    gap: 5,
  },
  moderateTagText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '700',
  },
  safeBox: {
    position: 'absolute',
    bottom: '24%',
    left: '10%',
    padding: 4,
  },
  safeTag: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#059669',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    gap: 6,
  },
  safeTagText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '700',
  },
  telemetryOverlay: {
    backgroundColor: 'rgba(15, 23, 42, 0.92)',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingHorizontal: 20,
    paddingTop: 18,
    paddingBottom: 24,
  },
  telemetryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  coordsCol: {
    gap: 4,
  },
  coordsMainRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  coordsMainText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
  telemetrySubText: {
    color: '#94A3B8',
    fontSize: 12,
  },
  captureBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#00875A',
    borderRadius: 16,
    height: 52,
    gap: 8,
    shadowColor: '#00875A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
    marginBottom: 12,
  },
  captureBtnText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  safetyGuidanceText: {
    textAlign: 'center',
    fontSize: 11,
    color: 'rgba(255,255,255,0.7)',
    lineHeight: 16,
  },
});

