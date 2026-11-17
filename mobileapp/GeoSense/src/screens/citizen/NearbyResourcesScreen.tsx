import { SafeAreaView } from 'react-native-safe-area-context';
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { Feather, Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { HeaderBar } from '@/components/HeaderBar';
import { useApp } from '@/context/AppContext';

export function NearbyResourcesScreen() {
  const { navigate } = useApp();
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [viewMode, setViewMode] = useState<'list' | 'map'>('list');

  const categories = ['All', 'Shelters', 'Hospitals', 'Rescue Teams', 'Relief Centres'];

  const resources = [
    {
      id: '1',
      title: 'Community Shelter A',
      type: 'Shelters',
      categoryDesc: 'Shelter · 84 / 150 places open',
      distance: '2.8 km',
      status: 'Available',
      icon: <Feather name="home" size={22} color="#00875A" />,
      hasAction: true,
    },
    {
      id: '2',
      title: 'Government School Shelter',
      type: 'Shelters',
      categoryDesc: 'Shelter · 120 / 200 places open',
      distance: '3.6 km',
      status: 'Available',
      icon: <MaterialCommunityIcons name="school-outline" size={22} color="#00875A" />,
      hasAction: false,
    },
    {
      id: '3',
      title: 'District Hospital',
      type: 'Hospitals',
      categoryDesc: 'Hospital · 24-hour emergency care',
      distance: '5.2 km',
      status: 'Available',
      icon: <MaterialCommunityIcons name="hospital-box-outline" size={22} color="#00875A" />,
      hasAction: false,
    },
    {
      id: '4',
      title: 'Rescue Team North',
      type: 'Rescue Teams',
      categoryDesc: 'Rescue team · Community response',
      distance: '4.1 km',
      status: 'Active',
      icon: <MaterialCommunityIcons name="shield-account-outline" size={22} color="#00875A" />,
      hasAction: false,
    },
    {
      id: '5',
      title: 'Relief Supply Centre',
      type: 'Relief Centres',
      categoryDesc: 'Relief centre · Food, water & first aid',
      distance: '6.3 km',
      status: 'Available',
      icon: <Feather name="box" size={22} color="#00875A" />,
      hasAction: false,
    },
  ];

  const filteredResources = resources.filter(
    (r) => selectedCategory === 'All' || r.type === selectedCategory
  );

  return (
    <SafeAreaView style={styles.safeArea} edges={['left', 'right']}>
      <HeaderBar title="Nearby resources" variant="sub-light" />

      {/* Location selector */}
      <View style={styles.locationBar}>
        <TouchableOpacity
          style={styles.locationSelector}
          onPress={() => navigate('map')}
          activeOpacity={0.7}>
          <Ionicons name="location-outline" size={18} color="#00875A" />
          <Text style={styles.locationText}>Cherrapunji, Meghalaya</Text>
          <Feather name="chevron-down" size={16} color="#00875A" />
        </TouchableOpacity>
      </View>

      {/* Category Pills */}
      <View style={styles.categoriesWrapper}>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.categoriesScroll}>
          {categories.map((c) => {
            const isSelected = selectedCategory === c;
            return (
              <TouchableOpacity
                key={c}
                style={[
                  styles.categoryPill,
                  isSelected && styles.categoryPillActive,
                ]}
                onPress={() => setSelectedCategory(c)}>
                <Text
                  style={[
                    styles.categoryPillText,
                    isSelected && styles.categoryPillTextActive,
                  ]}>
                  {c}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </View>

      {/* View Switcher and Radius */}
      <View style={styles.viewRow}>
        <View style={styles.listMapSwitch}>
          <TouchableOpacity
            style={[styles.switchOption, viewMode === 'list' && styles.switchOptionActive]}
            onPress={() => setViewMode('list')}>
            <Text style={[styles.switchText, viewMode === 'list' && styles.switchTextActive]}>
              List
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.switchOption, viewMode === 'map' && styles.switchOptionActive]}
            onPress={() => navigate('map')}>
            <Text style={[styles.switchText, viewMode === 'map' && styles.switchTextActive]}>
              Map
            </Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity style={styles.filterButton} activeOpacity={0.7}>
          <Feather name="sliders" size={14} color="#334155" />
          <Text style={styles.filterText}>Within 10 km</Text>
        </TouchableOpacity>
      </View>

      {/* Resources Cards List */}
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}>
        {filteredResources.map((item) => (
          <View
            key={item.id}
            style={[
              styles.resourceCard,
              item.hasAction && styles.resourceCardPrimary,
            ]}>
            <View style={styles.cardHeaderRow}>
              <View style={styles.cardIconBox}>{item.icon}</View>
              <View style={styles.cardInfo}>
                <Text style={styles.cardTitle}>{item.title}</Text>
                <Text style={styles.cardSubtitle}>{item.categoryDesc}</Text>
                <View style={styles.statusDistanceRow}>
                  <Text style={styles.distanceValue}>{item.distance}</Text>
                  <View style={styles.statusPill}>
                    <View style={styles.greenStatusDot} />
                    <Text style={styles.statusText}>{item.status}</Text>
                  </View>
                </View>
              </View>

              {!item.hasAction && (
                <TouchableOpacity
                  style={styles.navIconButton}
                  onPress={() => navigate('evacuation')}>
                  <Feather name="navigation" size={20} color="#00875A" />
                </TouchableOpacity>
              )}
            </View>

            {item.hasAction && (
              <TouchableOpacity
                style={styles.getDirectionsBtn}
                onPress={() => navigate('evacuation')}
                activeOpacity={0.85}>
                <MaterialCommunityIcons name="routes" size={20} color="#FFFFFF" />
                <Text style={styles.getDirectionsText}>Get Directions</Text>
              </TouchableOpacity>
            )}
          </View>
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  locationBar: {
    paddingHorizontal: 20,
    paddingTop: 10,
    paddingBottom: 8,
  },
  locationSelector: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  locationText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#00875A',
  },
  categoriesWrapper: {
    paddingVertical: 8,
  },
  categoriesScroll: {
    paddingHorizontal: 20,
    gap: 8,
  },
  categoryPill: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#F1F5F9',
  },
  categoryPillActive: {
    backgroundColor: '#0F172A',
  },
  categoryPillText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#475569',
  },
  categoryPillTextActive: {
    color: '#FFFFFF',
  },
  viewRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 10,
  },
  listMapSwitch: {
    flexDirection: 'row',
    backgroundColor: '#F1F5F9',
    borderRadius: 14,
    padding: 3,
  },
  switchOption: {
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 11,
  },
  switchOptionActive: {
    backgroundColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  switchText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#64748B',
  },
  switchTextActive: {
    color: '#0F172A',
    fontWeight: '700',
  },
  filterButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  filterText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#334155',
  },
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  contentContainer: {
    paddingHorizontal: 20,
    paddingTop: 10,
    paddingBottom: 95,
    gap: 14,
  },
  resourceCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 18,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
    elevation: 2,
  },
  resourceCardPrimary: {
    borderColor: '#A7F3D0',
    borderWidth: 1.5,
  },
  cardHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
  },
  cardIconBox: {
    width: 48,
    height: 48,
    borderRadius: 16,
    backgroundColor: '#E8F5E9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardInfo: {
    flex: 1,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#0F172A',
  },
  cardSubtitle: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
  statusDistanceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 6,
  },
  distanceValue: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0F172A',
  },
  statusPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  greenStatusDot: {
    width: 7,
    height: 7,
    borderRadius: 3.5,
    backgroundColor: '#10B981',
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#00875A',
  },
  navIconButton: {
    padding: 8,
  },
  getDirectionsBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#00875A',
    borderRadius: 14,
    height: 48,
    gap: 8,
    marginTop: 14,
    shadowColor: '#00875A',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.25,
    shadowRadius: 6,
    elevation: 3,
  },
  getDirectionsText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
});

