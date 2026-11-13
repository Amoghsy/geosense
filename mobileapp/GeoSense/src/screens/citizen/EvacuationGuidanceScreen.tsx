import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  ImageBackground,
  ScrollView,
  Alert,
} from 'react-native';
import { Feather, Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { HeaderBar } from '@/components/HeaderBar';
import { useApp } from '@/context/AppContext';

export function EvacuationGuidanceScreen() {
  const { navigate } = useApp();
  const [isNavigating, setIsNavigating] = useState(false);

  const handleCallEmergency = () => {
    Alert.alert(
      'Emergency Call (112)',
      'Calling emergency services at 112 for immediate dispatch and rescue support.',
      [{ text: 'OK' }]
    );
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <HeaderBar title="Evacuation guidance" variant="sub-light" />

      {/* Crimson Risk Banner */}
      <View style={styles.alertBanner}>
        <Ionicons name="warning-outline" size={18} color="#FFFFFF" />
        <Text style={styles.alertBannerText}>
          HIGH RISK AREA – EVACUATION GUIDANCE
        </Text>
      </View>

      <View style={styles.contentContainer}>
        {/* Map Viewport with Safe Route & Blocked Road */}
        <View style={styles.mapViewport}>
          <ImageBackground
            source={require('@/assets/images/design/satellite_map.jpg')}
            style={styles.mapImage}
            resizeMode="cover">
            
            {/* Mawmluh Shelter Pin */}
            <View style={styles.shelterPinContainer}>
              <View style={styles.shelterPinIcon}>
                <Feather name="home" size={18} color="#FFFFFF" />
              </View>
              <Text style={styles.shelterPinText}>Mawmluh</Text>
            </View>

            {/* Sohra Label */}
            <View style={styles.sohraLabelBox}>
              <Text style={styles.sohraLabelText}>SOHRA</Text>
            </View>

            {/* Blocked Road Pin */}
            <View style={styles.blockedRoadPin}>
              <MaterialCommunityIcons name="cancel" size={26} color="#FFFFFF" />
            </View>

            {/* Simulated Safe Route Path Line (SVG or styled bar) */}
            <View style={styles.safePathLine} />

            {/* User Blue Dot */}
            <View style={styles.userDotContainer}>
              <View style={styles.userDotPulse} />
              <View style={styles.userDotCore} />
            </View>

            {/* Floating Route Legend Badges on Map */}
            <View style={styles.routeBadgesRow}>
              <View style={styles.safeRouteBadge}>
                <View style={styles.greenDot} />
                <Text style={styles.safeRouteBadgeText}>Safe route</Text>
              </View>
              <View style={styles.blockedBadge}>
                <MaterialCommunityIcons name="cancel" size={14} color="#EF4444" />
                <Text style={styles.blockedBadgeText}>Blocked road</Text>
              </View>
            </View>

            {/* Map Tools */}
            <View style={styles.mapToolsRight}>
              <TouchableOpacity style={styles.toolBtn}>
                <Feather name="crosshair" size={18} color="#1E293B" />
              </TouchableOpacity>
              <TouchableOpacity style={styles.toolBtn}>
                <Feather name="plus" size={18} color="#1E293B" />
              </TouchableOpacity>
              <TouchableOpacity style={styles.toolBtn}>
                <Feather name="minus" size={18} color="#1E293B" />
              </TouchableOpacity>
            </View>
          </ImageBackground>
        </View>

        {/* Bottom Navigation Sheet */}
        <View style={styles.bottomSheet}>
          <View style={styles.handleBar} />

          <View style={styles.shelterHeaderRow}>
            <View style={styles.shelterIconBox}>
              <Feather name="home" size={26} color="#00875A" />
            </View>
            <View style={styles.shelterInfoCol}>
              <Text style={styles.nearestLabel}>Nearest Safe Shelter</Text>
              <Text style={styles.shelterTitle}>Community Shelter A</Text>
              <View style={styles.distanceTagRow}>
                <Text style={styles.distanceText}>2.8 km · 8 minutes</Text>
                <View style={styles.safeStatusPill}>
                  <View style={styles.safeDot} />
                  <Text style={styles.safeStatusText}>SAFE ROUTE</Text>
                </View>
              </View>
            </View>
          </View>

          <View style={styles.roadConditionRow}>
            <Text style={styles.roadCondLabel}>Road condition: Passable</Text>
          </View>

          {/* Alternate Route Row */}
          <View style={styles.alternateRow}>
            <Text style={styles.altText}>Alternate route via Mawmluh</Text>
            <Text style={styles.altStats}>4.2 km · 13 min</Text>
          </View>

          {/* Start Navigation Button */}
          <TouchableOpacity
            style={[
              styles.startNavButton,
              isNavigating && { backgroundColor: '#0D5C3A' },
            ]}
            onPress={() => setIsNavigating(!isNavigating)}
            activeOpacity={0.85}>
            <Feather
              name={isNavigating ? 'check-circle' : 'navigation'}
              size={18}
              color="#FFFFFF"
            />
            <Text style={styles.startNavText}>
              {isNavigating ? 'Navigating to Shelter A...' : 'Start Navigation'}
            </Text>
          </TouchableOpacity>

          {/* Secondary Action Row */}
          <View style={styles.secondaryActionsRow}>
            <TouchableOpacity
              style={styles.secActionButton}
              onPress={() => Alert.alert('Recalculating', 'Finding newest satellite route updates...')}
              activeOpacity={0.75}>
              <Feather name="rotate-cw" size={16} color="#0F172A" />
              <Text style={styles.secActionText}>Recalculate Route</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.secActionButton}
              onPress={() => navigate('resources')}
              activeOpacity={0.75}>
              <Feather name="shield" size={16} color="#0F172A" />
              <Text style={styles.secActionText}>Nearby Safe Zones</Text>
            </TouchableOpacity>
          </View>

          {/* Emergency Call Button */}
          <TouchableOpacity
            style={styles.emergencyButton}
            onPress={handleCallEmergency}
            activeOpacity={0.85}>
            <Feather name="phone-call" size={18} color="#FFFFFF" />
            <Text style={styles.emergencyText}>Emergency Call (112)</Text>
          </TouchableOpacity>

          <Text style={styles.disclaimerText}>
            Follow local authority instructions. Routes may change.
          </Text>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  alertBanner: {
    backgroundColor: '#991B1B',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    paddingHorizontal: 16,
    gap: 8,
  },
  alertBannerText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  contentContainer: {
    flex: 1,
  },
  mapViewport: {
    flex: 1,
  },
  mapImage: {
    flex: 1,
    position: 'relative',
  },
  shelterPinContainer: {
    position: 'absolute',
    top: '18%',
    left: '20%',
    alignItems: 'center',
  },
  shelterPinIcon: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: '#0D5C3A',
    borderWidth: 2,
    borderColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
  },
  shelterPinText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
    marginTop: 2,
    textShadowColor: 'rgba(0,0,0,0.8)',
    textShadowRadius: 3,
  },
  sohraLabelBox: {
    position: 'absolute',
    top: '38%',
    left: '36%',
  },
  sohraLabelText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '900',
    letterSpacing: 1,
    textShadowColor: 'rgba(0,0,0,0.8)',
    textShadowRadius: 4,
  },
  blockedRoadPin: {
    position: 'absolute',
    top: '44%',
    right: '25%',
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#EF4444',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: '#FFFFFF',
  },
  safePathLine: {
    position: 'absolute',
    top: '26%',
    left: '24%',
    width: 70,
    height: 120,
    borderLeftWidth: 5,
    borderBottomWidth: 5,
    borderLeftColor: '#10B981',
    borderBottomColor: '#10B981',
    borderBottomLeftRadius: 40,
    transform: [{ rotate: '20deg' }],
  },
  userDotContainer: {
    position: 'absolute',
    top: '52%',
    left: '42%',
    width: 30,
    height: 30,
    alignItems: 'center',
    justifyContent: 'center',
  },
  userDotPulse: {
    position: 'absolute',
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: 'rgba(37, 99, 235, 0.3)',
  },
  userDotCore: {
    width: 14,
    height: 14,
    borderRadius: 7,
    backgroundColor: '#2563EB',
    borderWidth: 2,
    borderColor: '#FFFFFF',
  },
  routeBadgesRow: {
    position: 'absolute',
    top: '42%',
    left: 16,
    flexDirection: 'row',
    gap: 8,
  },
  safeRouteBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 14,
    gap: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
  },
  greenDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#10B981',
  },
  safeRouteBadgeText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#065F46',
  },
  blockedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 14,
    gap: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
  },
  blockedBadgeText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#EF4444',
  },
  mapToolsRight: {
    position: 'absolute',
    right: 16,
    top: '20%',
    gap: 8,
  },
  toolBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.12,
    shadowRadius: 6,
  },
  bottomSheet: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -3 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 8,
  },
  handleBar: {
    width: 36,
    height: 4,
    borderRadius: 2,
    backgroundColor: '#CBD5E1',
    alignSelf: 'center',
    marginBottom: 12,
  },
  shelterHeaderRow: {
    flexDirection: 'row',
    gap: 14,
    alignItems: 'center',
  },
  shelterIconBox: {
    width: 52,
    height: 52,
    borderRadius: 16,
    backgroundColor: '#E8F5E9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  shelterInfoCol: {
    flex: 1,
  },
  nearestLabel: {
    fontSize: 12,
    color: '#64748B',
    fontWeight: '500',
  },
  shelterTitle: {
    fontSize: 19,
    fontWeight: '800',
    color: '#0F172A',
    marginTop: 1,
  },
  distanceTagRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 3,
  },
  distanceText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#00875A',
  },
  safeStatusPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#D1FAE5',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    gap: 4,
  },
  safeDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#10B981',
  },
  safeStatusText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#065F46',
  },
  roadConditionRow: {
    marginTop: 8,
    marginBottom: 10,
  },
  roadCondLabel: {
    fontSize: 12,
    color: '#64748B',
  },
  alternateRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
    marginBottom: 14,
  },
  altText: {
    fontSize: 13,
    color: '#475569',
  },
  altStats: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0F172A',
  },
  startNavButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#00875A',
    borderRadius: 16,
    height: 50,
    gap: 8,
    shadowColor: '#00875A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 3,
    marginBottom: 12,
  },
  startNavText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  secondaryActionsRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  secActionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F1F5F9',
    borderRadius: 14,
    height: 44,
    gap: 6,
  },
  secActionText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#0F172A',
  },
  emergencyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#EF4444',
    borderRadius: 16,
    height: 50,
    gap: 8,
    shadowColor: '#EF4444',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
    elevation: 2,
    marginBottom: 8,
  },
  emergencyText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
  disclaimerText: {
    textAlign: 'center',
    fontSize: 11,
    color: '#94A3B8',
  },
});

