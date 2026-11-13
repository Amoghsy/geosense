import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  ImageBackground,
  Switch,
  Alert,
} from 'react-native';
import { Feather, Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { useApp } from '@/context/AppContext';

export function ARFieldIntelligenceScreen() {
  const { goBack, navigate } = useApp();
  const [mode, setMode] = useState<'ar' | 'map'>('ar');
  const [riskOverlay, setRiskOverlay] = useState(true);

  return (
    <View style={styles.container}>
      <ImageBackground
        source={require('@/assets/images/design/ar_camera_view.jpg')}
        style={styles.bgImage}
        resizeMode="cover">
        
        <SafeAreaView style={styles.safeArea}>
          {/* Top Custom AR Navigation Bar */}
          <View style={styles.topBar}>
            <TouchableOpacity
              onPress={goBack}
              style={styles.backBtn}
              hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
              <Ionicons name="arrow-back" size={24} color="#FFFFFF" />
            </TouchableOpacity>

            <Text style={styles.arTitle}>AR Field Intelligence</Text>

            <TouchableOpacity
              style={styles.cameraIconBtn}
              onPress={() => Alert.alert('Snapshot', 'AR Field snapshot captured')}>
              <Feather name="camera" size={20} color="#FFFFFF" />
            </TouchableOpacity>
          </View>

          {/* AR Status HUD Row */}
          <View style={styles.hudStatusRow}>
            <View style={styles.activeTag}>
              <View style={styles.liveGreenDot} />
              <Text style={styles.activeTagText}>CAMERA ACTIVE · AR</Text>
            </View>
            <Text style={styles.gpsAccuracyText}>GPS accuracy ±4 m</Text>
          </View>

          {/* Floating High Risk Zone Card */}
          <View style={styles.riskZoneCard}>
            <View style={styles.riskZoneHeader}>
              <Ionicons name="warning-outline" size={16} color="#EF4444" />
              <Text style={styles.riskZoneCardTitle}>HIGH RISK ZONE</Text>
            </View>

            <View style={styles.statsRow}>
              <View style={styles.statCol}>
                <Text style={styles.statBigRed}>87%</Text>
                <Text style={styles.statLabel}>Landslide Probability</Text>
              </View>
              <View style={styles.statCol}>
                <Text style={styles.statMedRed}>HIGH</Text>
                <Text style={styles.statLabel}>Risk Level</Text>
              </View>
              <View style={styles.statCol}>
                <Text style={styles.statMedRed}>Next 6 Hours</Text>
                <Text style={styles.statLabel}>Predicted Window</Text>
              </View>
            </View>
          </View>

          {/* AR Overlays on Terrain */}
          {/* 1. Unstable Slope Red Polygon */}
          {riskOverlay && (
            <View style={styles.unstableSlopePolygon}>
              <View style={styles.unstableBadge}>
                <Text style={styles.unstableBadgeText}>UNSTABLE SLOPE</Text>
              </View>
            </View>
          )}

          {/* 2. Shelter Ridge Yellow Polygon */}
          <View style={styles.shelterPolygon}>
            <View style={styles.shelterBadge}>
              <Feather name="home" size={13} color="#FFFFFF" />
              <Text style={styles.shelterBadgeText}>Shelter A · 2.8 km</Text>
            </View>
          </View>

          {/* 3. Glowing Road Chevrons (^ ^ ^) */}
          <View style={styles.chevronsContainer}>
            <MaterialCommunityIcons name="chevron-up" size={42} color="rgba(16, 185, 129, 0.6)" />
            <MaterialCommunityIcons name="chevron-up" size={54} color="rgba(16, 185, 129, 0.8)" style={{ marginTop: -20 }} />
            <MaterialCommunityIcons name="chevron-up" size={72} color="#10B981" style={{ marginTop: -24 }} />
          </View>

          {/* Right Floating AR HUD Controls */}
          <View style={styles.rightHudControls}>
            <TouchableOpacity style={styles.hudToolBtn}>
              <MaterialCommunityIcons name="layers-outline" size={20} color="#1E293B" />
            </TouchableOpacity>
            <TouchableOpacity style={styles.hudToolBtn}>
              <MaterialCommunityIcons name="hospital-box-outline" size={20} color="#1E293B" />
            </TouchableOpacity>
            <TouchableOpacity style={styles.hudToolBtn}>
              <Feather name="navigation" size={20} color="#1E293B" />
            </TouchableOpacity>
          </View>

          {/* Bottom Controls Area */}
          <View style={styles.bottomControlsArea}>
            <View style={styles.modeAndToggleRow}>
              {/* AR / Map Switch */}
              <View style={styles.arMapToggle}>
                <TouchableOpacity
                  style={[styles.togglePill, mode === 'ar' && styles.togglePillActive]}
                  onPress={() => setMode('ar')}>
                  <Text style={[styles.toggleText, mode === 'ar' && styles.toggleTextActive]}>
                    AR
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.togglePill, mode === 'map' && styles.togglePillActive]}
                  onPress={() => {
                    setMode('map');
                    navigate('map');
                  }}>
                  <Text style={[styles.toggleText, mode === 'map' && styles.toggleTextActive]}>
                    Map
                  </Text>
                </TouchableOpacity>
              </View>

              {/* Risk Overlay Switch */}
              <View style={styles.switchWrapper}>
                <Text style={styles.switchLabel}>Risk overlay</Text>
                <Switch
                  value={riskOverlay}
                  onValueChange={setRiskOverlay}
                  trackColor={{ false: '#475569', true: '#10B981' }}
                  thumbColor="#FFFFFF"
                />
              </View>
            </View>

            {/* Circular Target / Shutter Button */}
            <TouchableOpacity
              style={styles.shutterButton}
              onPress={() => Alert.alert('Scanned', 'Terrain analysis updated in real time')}
              activeOpacity={0.8}>
              <View style={styles.shutterInnerCircle}>
                <MaterialCommunityIcons name="line-scan" size={28} color="#00875A" />
              </View>
            </TouchableOpacity>

            <Text style={styles.scanningText}>Scanning terrain · Keep camera steady</Text>

            {/* Safety Distance Alert Box */}
            <View style={styles.bottomAlertBox}>
              <Ionicons name="shield-outline" size={18} color="#DC2626" />
              <Text style={styles.bottomAlertText}>
                Maintain a safe distance. Avoid unstable slopes.
              </Text>
            </View>
          </View>
        </SafeAreaView>
      </ImageBackground>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  bgImage: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
    justifyContent: 'space-between',
  },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 10,
  },
  backBtn: {
    padding: 6,
  },
  arTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    textShadowColor: 'rgba(0,0,0,0.8)',
    textShadowRadius: 6,
  },
  cameraIconBtn: {
    padding: 6,
  },
  hudStatusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    marginTop: 8,
  },
  activeTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  liveGreenDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#10B981',
  },
  activeTagText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: 0.5,
    textShadowColor: 'rgba(0,0,0,0.8)',
    textShadowRadius: 4,
  },
  gpsAccuracyText: {
    fontSize: 11,
    color: 'rgba(255,255,255,0.85)',
    fontWeight: '600',
    textShadowColor: 'rgba(0,0,0,0.8)',
    textShadowRadius: 4,
  },
  riskZoneCard: {
    backgroundColor: 'rgba(255,255,255,0.92)',
    marginHorizontal: 16,
    borderRadius: 18,
    padding: 16,
    marginTop: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
  },
  riskZoneHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 8,
  },
  riskZoneCardTitle: {
    fontSize: 12,
    fontWeight: '800',
    color: '#DC2626',
    letterSpacing: 0.5,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
  },
  statCol: {
    flex: 1,
  },
  statBigRed: {
    fontSize: 32,
    fontWeight: '900',
    color: '#EF4444',
  },
  statMedRed: {
    fontSize: 16,
    fontWeight: '800',
    color: '#EF4444',
  },
  statLabel: {
    fontSize: 10,
    color: '#64748B',
    marginTop: 2,
  },
  unstableSlopePolygon: {
    position: 'absolute',
    top: '32%',
    left: '6%',
    width: '40%',
    height: '24%',
    borderColor: '#EF4444',
    borderWidth: 2,
    backgroundColor: 'rgba(239, 68, 68, 0.22)',
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  unstableBadge: {
    backgroundColor: '#DC2626',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  unstableBadgeText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  shelterPolygon: {
    position: 'absolute',
    top: '35%',
    right: '6%',
    width: '34%',
    height: '22%',
    borderColor: '#EAB308',
    borderWidth: 2,
    backgroundColor: 'rgba(234, 179, 8, 0.2)',
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  shelterBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#065F46',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    gap: 4,
  },
  shelterBadgeText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '700',
  },
  chevronsContainer: {
    position: 'absolute',
    bottom: '22%',
    alignSelf: 'center',
    alignItems: 'center',
  },
  rightHudControls: {
    position: 'absolute',
    right: 16,
    top: '46%',
    gap: 10,
  },
  hudToolBtn: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
  },
  bottomControlsArea: {
    paddingHorizontal: 20,
    paddingBottom: 20,
    alignItems: 'center',
  },
  modeAndToggleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    width: '100%',
    marginBottom: 16,
  },
  arMapToggle: {
    flexDirection: 'row',
    backgroundColor: 'rgba(15, 23, 42, 0.75)',
    borderRadius: 20,
    padding: 3,
  },
  togglePill: {
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 16,
  },
  togglePillActive: {
    backgroundColor: '#FFFFFF',
  },
  toggleText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  toggleTextActive: {
    color: '#0F172A',
  },
  switchWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: 'rgba(15, 23, 42, 0.75)',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 20,
  },
  switchLabel: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  shutterButton: {
    width: 66,
    height: 66,
    borderRadius: 33,
    borderWidth: 3,
    borderColor: '#FFFFFF',
    backgroundColor: 'rgba(255,255,255,0.3)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  shutterInnerCircle: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  scanningText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '500',
    marginBottom: 14,
    textShadowColor: 'rgba(0,0,0,0.8)',
    textShadowRadius: 4,
  },
  bottomAlertBox: {
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderRadius: 16,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    width: '100%',
    gap: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 6,
  },
  bottomAlertText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1E293B',
    flex: 1,
  },
});

