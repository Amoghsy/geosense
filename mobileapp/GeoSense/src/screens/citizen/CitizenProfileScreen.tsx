import { SafeAreaView } from 'react-native-safe-area-context';
import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
} from 'react-native';
import { Feather, Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { HeaderBar } from '@/components/HeaderBar';
import { useApp } from '@/context/AppContext';

export function CitizenProfileScreen() {
  const { navigate, citizenName, citizenPhone, setPortalTab, logoutCitizen } = useApp();

  const menuItems = [
    {
      icon: <Ionicons name="location-outline" size={20} color="#334155" />,
      title: 'My Locations',
      subtitle: 'Saved locations & location-specific warnings',
      action: () => navigate('map'),
    },
    {
      icon: <Ionicons name="notifications-outline" size={20} color="#334155" />,
      title: 'Alert Preferences',
      subtitle: 'Push notifications, SMS & email',
      action: () => navigate('alerts'),
    },
    {
      icon: <Feather name="map" size={20} color="#334155" />,
      title: 'Offline Maps',
      subtitle: 'Downloaded terrain & safety information',
      action: () => navigate('offline-maps'),
    },
    {
      icon: <MaterialCommunityIcons name="translate" size={20} color="#334155" />,
      title: 'Language Preferences',
      subtitle: 'English, Hindi, Assamese, Khasi, Garo & more',
      action: () => {},
    },
    {
      icon: <Ionicons name="people-outline" size={20} color="#334155" />,
      title: 'Emergency Contacts',
      subtitle: 'Family, local teams & emergency helplines',
      action: () => {},
    },
    {
      icon: <Feather name="book-open" size={20} color="#334155" />,
      title: 'Help & Guidelines',
      subtitle: 'Prepare, evacuate & report safely',
      action: () => {},
    },
    {
      icon: <Feather name="info" size={20} color="#334155" />,
      title: 'About GeoSense',
      subtitle: 'Terrain intelligence · Version 1.0.0',
      action: () => {},
    },
    {
      icon: <Feather name="shield" size={20} color="#334155" />,
      title: 'Privacy & Security',
      subtitle: 'Location permissions & personal data',
      action: () => {},
    },
  ];

  return (
    <SafeAreaView style={styles.safeArea} edges={['left', 'right']}>
      <HeaderBar title="Profile & Settings" variant="sub-light" />

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}>
        
        {/* User Profile Card */}
        <View style={styles.userCard}>
          <Image
            source={require('@/assets/images/design/citizen_avatar.jpg')}
            style={styles.avatarImage}
          />
          <View style={styles.userInfo}>
            <Text style={styles.userName}>{citizenName || 'Aiban Khonglah'}</Text>
            <Text style={styles.userPhone}>{citizenPhone || '+91 98630 01482'}</Text>
            <View style={styles.roleBadge}>
              <Text style={styles.roleBadgeText}>CITIZEN</Text>
            </View>
          </View>
          <TouchableOpacity style={styles.editProfileBtn}>
            <Feather name="edit-2" size={18} color="#64748B" />
          </TouchableOpacity>
        </View>

        {/* Menu list items */}
        <View style={styles.menuContainer}>
          {menuItems.map((item, idx) => (
            <TouchableOpacity
              key={idx}
              style={[
                styles.menuRow,
                idx === menuItems.length - 1 && { borderBottomWidth: 0 },
              ]}
              onPress={item.action}
              activeOpacity={0.7}>
              <View style={styles.menuIconBox}>{item.icon}</View>
              <View style={styles.menuContent}>
                <Text style={styles.menuTitle}>{item.title}</Text>
                <Text style={styles.menuSubtitle}>{item.subtitle}</Text>
              </View>
              <Feather name="chevron-right" size={18} color="#94A3B8" />
            </TouchableOpacity>
          ))}
        </View>

        {/* Offline Maps Available Banner */}
        <TouchableOpacity
          style={styles.offlineBanner}
          onPress={() => navigate('offline-maps')}
          activeOpacity={0.8}>
          <View style={styles.offlineBannerIconBox}>
            <Feather name="download" size={20} color="#065F46" />
          </View>
          <View style={styles.offlineBannerInfo}>
            <Text style={styles.offlineBannerTitle}>Offline Maps Available</Text>
            <Text style={styles.offlineBannerSub}>
              Meghalaya downloaded · View offline readiness →
            </Text>
          </View>
        </TouchableOpacity>

        {/* Switch to Field Officer Workspace */}
        <TouchableOpacity
          style={styles.officerPortalButton}
          onPress={() => {
            setPortalTab('officer');
            navigate('login-portal');
          }}
          activeOpacity={0.85}>
          <Feather name="shield" size={18} color="#0D5C3A" />
          <Text style={styles.officerPortalText}>Field Officer Portal Login</Text>
        </TouchableOpacity>

        {/* Sign Out / Return to Access Portal */}
        <TouchableOpacity
          style={styles.signOutButton}
          onPress={logoutCitizen}
          activeOpacity={0.85}>
          <Feather name="log-out" size={18} color="#DC2626" />
          <Text style={styles.signOutButtonText}>Sign Out / Switch Portal</Text>
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
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 95,
  },
  userCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 18,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
    elevation: 2,
    gap: 14,
  },
  avatarImage: {
    width: 60,
    height: 60,
    borderRadius: 30,
  },
  userInfo: {
    flex: 1,
  },
  userName: {
    fontSize: 18,
    fontWeight: '800',
    color: '#0F172A',
  },
  userPhone: {
    fontSize: 13,
    color: '#64748B',
    marginTop: 2,
  },
  roleBadge: {
    backgroundColor: '#D1FAE5',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
    alignSelf: 'flex-start',
    marginTop: 6,
  },
  roleBadgeText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#065F46',
    letterSpacing: 0.5,
  },
  editProfileBtn: {
    padding: 8,
  },
  menuContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    paddingHorizontal: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
    elevation: 2,
  },
  menuRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#F8FAFC',
    gap: 14,
  },
  menuIconBox: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: '#F1F5F9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  menuContent: {
    flex: 1,
  },
  menuTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
  },
  menuSubtitle: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 2,
  },
  offlineBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#D1FAE5',
    borderRadius: 16,
    padding: 16,
    gap: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#A7F3D0',
  },
  offlineBannerIconBox: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  offlineBannerInfo: {
    flex: 1,
  },
  offlineBannerTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#065F46',
  },
  offlineBannerSub: {
    fontSize: 12,
    color: '#047857',
    marginTop: 2,
  },
  officerPortalButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    height: 50,
    borderWidth: 1.5,
    borderColor: '#0D5C3A',
    gap: 8,
  },
  officerPortalText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0D5C3A',
  },
  signOutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FEF2F2',
    borderRadius: 16,
    height: 50,
    borderWidth: 1,
    borderColor: '#FEE2E2',
    marginTop: 12,
    gap: 8,
  },
  signOutButtonText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#DC2626',
  },
});

