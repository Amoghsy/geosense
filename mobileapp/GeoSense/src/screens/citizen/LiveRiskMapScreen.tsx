import { SafeAreaView } from 'react-native-safe-area-context';
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  TextInput,
  Dimensions,
} from 'react-native';
import { Feather, Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { HeaderBar } from '@/components/HeaderBar';
import { useApp } from '@/context/AppContext';

const { width } = Dimensions.get('window');

export function LiveRiskMapScreen() {
  const { navigate } = useApp();
  const [activeLayer, setActiveLayer] = useState<'satellite' | 'risk' | 'historical'>('risk');
  const [searchQuery, setSearchQuery] = useState('');

  return (
    <SafeAreaView style={styles.safeArea} edges={['left', 'right']}>
      <HeaderBar title="Live Risk Map" variant="sub-light" />

      <View style={styles.mapContainer}>
        {/* Real Satellite Map Image from PDF Asset */}
        <Image
          source={require('@/assets/images/design/satellite_map.jpg')}
          style={StyleSheet.absoluteFill}
          resizeMode="cover"
        />
          
          {/* Top Search Bar & Layer Chips */}
          <View style={styles.topControls}>
            <View style={styles.searchBar}>
              <Feather name="search" size={18} color="#64748B" />
              <TextInput
                style={styles.searchInput}
                placeholder="Search location"
                placeholderTextColor="#94A3B8"
                value={searchQuery}
                onChangeText={setSearchQuery}
              />
              {searchQuery.length > 0 && (
                <TouchableOpacity onPress={() => setSearchQuery('')}>
                  <Feather name="x" size={16} color="#64748B" />
                </TouchableOpacity>
              )}
            </View>

            {/* Layer Chips */}
            <View style={styles.layerChipsRow}>
              <TouchableOpacity
                style={[
                  styles.chipButton,
                  activeLayer === 'satellite' && styles.chipButtonActive,
                ]}
                onPress={() => setActiveLayer('satellite')}>
                <MaterialCommunityIcons
                  name="satellite-variant"
                  size={14}
                  color={activeLayer === 'satellite' ? '#FFFFFF' : '#1E293B'}
                />
                <Text
                  style={[
                    styles.chipText,
                    activeLayer === 'satellite' && styles.chipTextActive,
                  ]}>
                  Satellite
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[
                  styles.chipButton,
                  activeLayer === 'risk' && styles.chipButtonActive,
                ]}
                onPress={() => setActiveLayer('risk')}>
                <Feather
                  name="check"
                  size={14}
                  color={activeLayer === 'risk' ? '#FFFFFF' : '#1E293B'}
                />
                <Text
                  style={[
                    styles.chipText,
                    activeLayer === 'risk' && styles.chipTextActive,
                  ]}>
                  Risk
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[
                  styles.chipButton,
                  activeLayer === 'historical' && styles.chipButtonActive,
                ]}
                onPress={() => setActiveLayer('historical')}>
                <Feather
                  name="clock"
                  size={14}
                  color={activeLayer === 'historical' ? '#FFFFFF' : '#1E293B'}
                />
                <Text
                  style={[
                    styles.chipText,
                    activeLayer === 'historical' && styles.chipTextActive,
                  ]}>
                  Historical
                </Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Interactive Zone Polygons and Pins Overlay */}
          {/* Mawmluh Green Zone */}
          <View style={[styles.polygonZone, styles.mawmluhZone]}>
            <View style={styles.zoneTag}>
              <Feather name="shield" size={14} color="#10B981" />
              <Text style={styles.zoneLabel}>Mawmluh</Text>
            </View>
          </View>

          {/* Sohra Orange Zone */}
          <View style={[styles.polygonZone, styles.sohraZone]}>
            <Text style={styles.sohraLabel}>SOHRA</Text>
          </View>

          {/* Mawsmai Yellow Zone */}
          <View style={[styles.polygonZone, styles.mawsmaiZone]}>
            <Text style={styles.mawsmaiLabel}>Mawsmai</Text>
          </View>

          {/* NH-206 Critical Zone */}
          <View style={[styles.polygonZone, styles.criticalZone]}>
            <Ionicons name="warning" size={18} color="#EF4444" />
            <Text style={styles.criticalLabel}>NH-206</Text>
          </View>

          {/* User Location Radar Pulse Pin */}
          <View style={styles.userLocationPulseContainer}>
            <View style={styles.radarPulseOuter} />
            <View style={styles.radarPulseInner} />
            <View style={styles.radarDot} />
          </View>

          {/* Right Floating Control Tools */}
          <View style={styles.floatingControlsRight}>
            <TouchableOpacity style={styles.toolButton}>
              <Feather name="crosshair" size={18} color="#1E293B" />
            </TouchableOpacity>
            <TouchableOpacity style={styles.toolButton}>
              <Feather name="plus" size={18} color="#1E293B" />
            </TouchableOpacity>
            <TouchableOpacity style={styles.toolButton}>
              <Feather name="minus" size={18} color="#1E293B" />
            </TouchableOpacity>
            <TouchableOpacity style={styles.toolButton}>
              <MaterialCommunityIcons name="image-filter-hdr" size={18} color="#1E293B" />
            </TouchableOpacity>
            <TouchableOpacity style={[styles.toolButton, { backgroundColor: '#FEE2E2' }]}>
              <Ionicons name="warning" size={18} color="#EF4444" />
            </TouchableOpacity>
          </View>

          {/* Map Risk Legend Bar */}
          <View style={styles.legendBar}>
            <View style={styles.legendItem}>
              <View style={[styles.legendDot, { backgroundColor: '#10B981' }]} />
              <Text style={styles.legendText}>Low</Text>
            </View>
            <View style={styles.legendItem}>
              <View style={[styles.legendDot, { backgroundColor: '#F59E0B' }]} />
              <Text style={styles.legendText}>Moderate</Text>
            </View>
            <View style={styles.legendItem}>
              <View style={[styles.legendDot, { backgroundColor: '#EF4444' }]} />
              <Text style={styles.legendText}>High</Text>
            </View>
            <View style={styles.legendItem}>
              <View style={[styles.legendDot, { backgroundColor: '#991B1B' }]} />
              <Text style={styles.legendText}>Critical</Text>
            </View>
          </View>

          {/* Bottom Sheet Card */}
          <View style={styles.bottomSheet}>
            <View style={styles.sheetTopRow}>
              <View>
                <Text style={styles.sheetLocationTitle}>Cherrapunji</Text>
                <Text style={styles.sheetLocationSub}>Meghalaya · Current location</Text>
              </View>
              <View style={styles.highPill}>
                <View style={styles.highDot} />
                <Text style={styles.highPillText}>HIGH</Text>
              </View>
            </View>

            <View style={styles.sheetStatsRow}>
              <Text style={styles.sheetRiskNum}>87%</Text>
              <View style={styles.sheetStatsDetails}>
                <View style={styles.increasingRow}>
                  <Feather name="trending-up" size={14} color="#EF4444" />
                  <Text style={styles.increasingText}>Increasing</Text>
                </View>
                <Text style={styles.rainfallText}>Rainfall 112 mm / 24h</Text>
              </View>
              <Feather name="cloud-rain" size={28} color="#64748B" />
            </View>

            <TouchableOpacity
              style={styles.viewDetailsButton}
              onPress={() => navigate('location-details')}
              activeOpacity={0.85}>
              <Text style={styles.viewDetailsText}>View Details</Text>
              <Feather name="arrow-right" size={18} color="#FFFFFF" />
            </TouchableOpacity>

            <Text style={styles.mapDisclaimer}>Demo data · Not a live safety advisory</Text>
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
  mapContainer: {
    flex: 1,
  },
  mapImage: {
    flex: 1,
    position: 'relative',
  },
  topControls: {
    paddingHorizontal: 16,
    paddingTop: 12,
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    paddingHorizontal: 16,
    height: 46,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
    gap: 10,
  },
  searchInput: {
    flex: 1,
    fontSize: 15,
    color: '#0F172A',
  },
  layerChipsRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 10,
  },
  chipButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 20,
    gap: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  chipButtonActive: {
    backgroundColor: '#0D5C3A',
  },
  chipText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1E293B',
  },
  chipTextActive: {
    color: '#FFFFFF',
  },
  polygonZone: {
    position: 'absolute',
    borderRadius: 16,
    borderWidth: 2,
    justifyContent: 'center',
    alignItems: 'center',
  },
  mawmluhZone: {
    top: '20%',
    left: '8%',
    width: 110,
    height: 90,
    borderColor: '#10B981',
    backgroundColor: 'rgba(16, 185, 129, 0.25)',
  },
  zoneTag: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.9)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 12,
    gap: 4,
  },
  zoneLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#065F46',
  },
  sohraZone: {
    top: '36%',
    left: '28%',
    width: 140,
    height: 110,
    borderColor: '#F59E0B',
    backgroundColor: 'rgba(245, 158, 11, 0.22)',
  },
  sohraLabel: {
    color: '#FFFFFF',
    fontWeight: '900',
    fontSize: 15,
    letterSpacing: 1,
    textShadowColor: 'rgba(0,0,0,0.6)',
    textShadowRadius: 4,
  },
  mawsmaiZone: {
    top: '24%',
    right: '8%',
    width: 100,
    height: 80,
    borderColor: '#EAB308',
    backgroundColor: 'rgba(234, 179, 8, 0.2)',
  },
  mawsmaiLabel: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 12,
    textShadowColor: 'rgba(0,0,0,0.6)',
    textShadowRadius: 3,
  },
  criticalZone: {
    top: '46%',
    right: '12%',
    width: 80,
    height: 70,
    borderColor: '#EF4444',
    backgroundColor: 'rgba(239, 68, 68, 0.35)',
  },
  criticalLabel: {
    color: '#FFFFFF',
    fontWeight: '800',
    fontSize: 11,
    marginTop: 2,
    textShadowColor: 'rgba(0,0,0,0.6)',
    textShadowRadius: 3,
  },
  userLocationPulseContainer: {
    position: 'absolute',
    top: '48%',
    left: '42%',
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  radarPulseOuter: {
    position: 'absolute',
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(37, 99, 235, 0.2)',
  },
  radarPulseInner: {
    position: 'absolute',
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: 'rgba(37, 99, 235, 0.35)',
  },
  radarDot: {
    width: 14,
    height: 14,
    borderRadius: 7,
    backgroundColor: '#2563EB',
    borderWidth: 2.5,
    borderColor: '#FFFFFF',
  },
  floatingControlsRight: {
    position: 'absolute',
    right: 16,
    top: '30%',
    gap: 8,
  },
  toolButton: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.12,
    shadowRadius: 6,
    elevation: 3,
  },
  legendBar: {
    position: 'absolute',
    bottom: 236,
    left: 16,
    right: 16,
    backgroundColor: 'rgba(255,255,255,0.92)',
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 8,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  legendText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#334155',
  },
  bottomSheet: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingHorizontal: 20,
    paddingTop: 18,
    paddingBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -3 },
    shadowOpacity: 0.12,
    shadowRadius: 10,
    elevation: 8,
  },
  sheetTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  sheetLocationTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#0F172A',
  },
  sheetLocationSub: {
    fontSize: 13,
    color: '#64748B',
    marginTop: 2,
  },
  highPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEE2E2',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 5,
  },
  highDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#EF4444',
  },
  highPillText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#DC2626',
  },
  sheetStatsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginVertical: 14,
  },
  sheetRiskNum: {
    fontSize: 40,
    fontWeight: '900',
    color: '#EF4444',
  },
  sheetStatsDetails: {
    flex: 1,
    marginLeft: 16,
  },
  increasingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  increasingText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#EF4444',
  },
  rainfallText: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
  viewDetailsButton: {
    backgroundColor: '#00875A',
    borderRadius: 16,
    height: 50,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    shadowColor: '#00875A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 10,
    elevation: 3,
  },
  viewDetailsText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  mapDisclaimer: {
    textAlign: 'center',
    fontSize: 11,
    color: '#94A3B8',
    marginTop: 10,
  },
});

