import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Platform } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons, Feather } from '@expo/vector-icons';
import { useApp, TabName } from '@/context/AppContext';

export function BottomNavBar() {
  const { role, activeTab, navigate, currentScreen } = useApp();
  const insets = useSafeAreaInsets();

  // Do not show bottom nav on full-screen flows like Login Portal, Officer Login, AR view full screen, or step-by-step reporting
  const isFullScreenFlow =
    currentScreen === 'login-portal' ||
    currentScreen === 'officer-login' ||
    currentScreen === 'ar-view' ||
    currentScreen === 'officer-ar' ||
    currentScreen === 'report-incident-1' ||
    currentScreen === 'report-incident-2' ||
    currentScreen === 'report-incident-success';

  if (isFullScreenFlow) {
    return null;
  }

  // Dynamic bottom padding adapting to Android navigation bar and iOS home indicator
  const bottomPadding = Math.max(insets.bottom, Platform.OS === 'android' ? 14 : 8);

  const handleTabPress = (tab: TabName) => {
    if (role === 'citizen') {
      if (tab === 'home') navigate('citizen-home');
      else if (tab === 'map') navigate('map');
      else if (tab === 'alerts') navigate('alerts');
      else if (tab === 'profile') navigate('profile');
    } else {
      if (tab === 'home') navigate('officer-home');
      else if (tab === 'missions') navigate('officer-mission');
      else if (tab === 'alerts') navigate('officer-alerts');
      else if (tab === 'profile') navigate('officer-profile');
    }
  };

  const isCitizen = role === 'citizen';

  return (
    <View style={[styles.container, { paddingBottom: bottomPadding, height: 54 + bottomPadding }]}>
      {/* Tab 1: Home */}
      <TouchableOpacity
        style={styles.tabItem}
        onPress={() => handleTabPress('home')}
        activeOpacity={0.7}>
        <View style={[styles.iconWrapper, activeTab === 'home' && styles.iconActiveWrapper]}>
          <Ionicons
            name={activeTab === 'home' ? 'home' : 'home-outline'}
            size={22}
            color={activeTab === 'home' ? '#00875A' : '#64748B'}
          />
        </View>
        <Text style={[styles.tabLabel, activeTab === 'home' && styles.tabLabelActive]}>
          Home
        </Text>
      </TouchableOpacity>

      {/* Tab 2: Map (Citizen) or Missions (Officer) */}
      {isCitizen ? (
        <TouchableOpacity
          style={styles.tabItem}
          onPress={() => handleTabPress('map')}
          activeOpacity={0.7}>
          <View style={[styles.iconWrapper, activeTab === 'map' && styles.iconActiveWrapper]}>
            <Ionicons
              name={activeTab === 'map' ? 'map' : 'map-outline'}
              size={22}
              color={activeTab === 'map' ? '#00875A' : '#64748B'}
            />
          </View>
          <Text style={[styles.tabLabel, activeTab === 'map' && styles.tabLabelActive]}>
            Map
          </Text>
        </TouchableOpacity>
      ) : (
        <TouchableOpacity
          style={styles.tabItem}
          onPress={() => handleTabPress('missions')}
          activeOpacity={0.7}>
          <View style={[styles.iconWrapper, activeTab === 'missions' && styles.iconActiveWrapper]}>
            <Feather
              name="target"
              size={21}
              color={activeTab === 'missions' ? '#0D5C3A' : '#64748B'}
            />
          </View>
          <Text style={[styles.tabLabel, activeTab === 'missions' && styles.tabLabelActive]}>
            Missions
          </Text>
        </TouchableOpacity>
      )}

      {/* Tab 3: Alerts */}
      <TouchableOpacity
        style={styles.tabItem}
        onPress={() => handleTabPress('alerts')}
        activeOpacity={0.7}>
        <View style={[styles.iconWrapper, activeTab === 'alerts' && styles.iconActiveWrapper]}>
          <Ionicons
            name={activeTab === 'alerts' ? 'notifications' : 'notifications-outline'}
            size={22}
            color={activeTab === 'alerts' ? '#00875A' : '#64748B'}
          />
        </View>
        <Text style={[styles.tabLabel, activeTab === 'alerts' && styles.tabLabelActive]}>
          Alerts
        </Text>
      </TouchableOpacity>

      {/* Tab 4: Profile */}
      <TouchableOpacity
        style={styles.tabItem}
        onPress={() => handleTabPress('profile')}
        activeOpacity={0.7}>
        <View style={[styles.iconWrapper, activeTab === 'profile' && styles.iconActiveWrapper]}>
          <Ionicons
            name={activeTab === 'profile' ? 'person' : 'person-outline'}
            size={22}
            color={activeTab === 'profile' ? '#00875A' : '#64748B'}
          />
        </View>
        <Text style={[styles.tabLabel, activeTab === 'profile' && styles.tabLabelActive]}>
          Profile
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    paddingTop: 6,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
    alignItems: 'center',
    justifyContent: 'space-around',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 8,
  },
  tabItem: {
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
  },
  iconWrapper: {
    width: 44,
    height: 28,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconActiveWrapper: {
    backgroundColor: '#D1FAE5',
  },
  tabLabel: {
    fontSize: 11,
    fontWeight: '500',
    color: '#64748B',
    marginTop: 2,
  },
  tabLabelActive: {
    color: '#00875A',
    fontWeight: '700',
  },
});
