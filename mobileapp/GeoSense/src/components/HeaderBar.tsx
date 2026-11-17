import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Image, Platform, StatusBar as RNStatusBar } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useApp } from '@/context/AppContext';
import { GeoSenseLogo } from './GeoSenseLogo';

interface HeaderBarProps {
  title?: string;
  subtitle?: string;
  variant?: 'citizen-main' | 'sub-light' | 'officer-main' | 'officer-dark';
  rightAction?: React.ReactNode;
  showBack?: boolean;
}

export function HeaderBar({
  title,
  subtitle,
  variant = 'sub-light',
  rightAction,
  showBack = true,
}: HeaderBarProps) {
  const { goBack, navigate } = useApp();
  const insets = useSafeAreaInsets();
  
  // Robust top inset ensuring full clearance of punch-hole cameras (Pixel 9, etc.), status bar icons, and Dynamic Islands
  const topInset = Math.max(
    insets.top,
    Platform.OS === 'android' ? Math.max(RNStatusBar.currentHeight || 0, 46) : 44
  );

  // 1. Citizen Main Header (Logo, Bell, Avatar)
  if (variant === 'citizen-main') {
    return (
      <View style={[styles.citizenMainContainer, { paddingTop: topInset + 8 }]}>
        <StatusBar style="dark" />
        <GeoSenseLogo size={28} textSize={22} color="#00A86B" textColor="#0F172A" />
        <View style={styles.rightIconsRow}>
          <TouchableOpacity
            style={styles.iconButton}
            onPress={() => navigate('alerts')}
            activeOpacity={0.7}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
            <Ionicons name="notifications-outline" size={24} color="#0F172A" />
            <View style={styles.unreadDot} />
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.avatarButton}
            onPress={() => navigate('profile')}
            activeOpacity={0.8}>
            <Image
              source={require('@/assets/images/design/citizen_avatar.jpg')}
              style={styles.avatar}
            />
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // 2. Officer Main Header (Dark green, Logo, Bell)
  if (variant === 'officer-main') {
    return (
      <View style={[styles.officerMainContainer, { paddingTop: topInset + 8 }]}>
        <StatusBar style="light" />
        <GeoSenseLogo size={28} textSize={22} color="#10B981" textColor="#FFFFFF" />
        <View style={styles.rightIconsRow}>
          <TouchableOpacity
            style={styles.iconButton}
            onPress={() => navigate('officer-alerts')}
            activeOpacity={0.7}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
            <Ionicons name="notifications-outline" size={24} color="#FFFFFF" />
            <View style={[styles.unreadDot, { backgroundColor: '#EF4444' }]} />
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // 3. Officer Sub-screen Dark Header
  if (variant === 'officer-dark') {
    return (
      <View style={[styles.officerDarkContainer, { paddingTop: topInset + 8 }]}>
        <StatusBar style="light" />
        <View style={styles.headerLeft}>
          {showBack && (
            <TouchableOpacity onPress={goBack} style={styles.backButton} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
              <Ionicons name="arrow-back" size={24} color="#FFFFFF" />
            </TouchableOpacity>
          )}
          <View style={styles.titleColumn}>
            <Text style={styles.officerTitle} numberOfLines={1}>{title}</Text>
            {subtitle && <Text style={styles.officerSubtitle} numberOfLines={1}>{subtitle}</Text>}
          </View>
        </View>
        <View style={styles.headerRight}>
          {rightAction || (
            <TouchableOpacity style={styles.iconButton} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
              <Ionicons name="ellipsis-vertical" size={20} color="#FFFFFF" />
            </TouchableOpacity>
          )}
        </View>
      </View>
    );
  }

  // 4. Citizen / Sub-screen Light Header
  return (
    <View style={[styles.subLightContainer, { paddingTop: topInset + 8 }]}>
      <StatusBar style="dark" />
      <View style={styles.headerLeft}>
        {showBack && (
          <TouchableOpacity onPress={goBack} style={styles.backButton} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
            <Ionicons name="arrow-back" size={24} color="#0F172A" />
          </TouchableOpacity>
        )}
        <View style={styles.titleColumn}>
          <Text style={styles.subTitle} numberOfLines={1}>{title}</Text>
          {subtitle && <Text style={styles.subSubtitle} numberOfLines={1}>{subtitle}</Text>}
        </View>
      </View>
      <View style={styles.headerRight}>
        {rightAction || (
          <TouchableOpacity style={styles.iconButton} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
            <Ionicons name="ellipsis-vertical" size={20} color="#0F172A" />
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  citizenMainContainer: {
    paddingHorizontal: 20,
    paddingBottom: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  officerMainContainer: {
    paddingHorizontal: 20,
    paddingBottom: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#0D5C3A',
  },
  subLightContainer: {
    paddingHorizontal: 16,
    paddingBottom: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  officerDarkContainer: {
    paddingHorizontal: 16,
    paddingBottom: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#0D5C3A',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: 12,
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  backButton: {
    padding: 4,
  },
  titleColumn: {
    flex: 1,
  },
  subTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0F172A',
    letterSpacing: -0.2,
  },
  subSubtitle: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
  officerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: -0.2,
  },
  officerSubtitle: {
    fontSize: 11,
    fontWeight: '600',
    color: '#A7F3D0',
    letterSpacing: 0.5,
    marginTop: 2,
    textTransform: 'uppercase',
  },
  rightIconsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
  },
  iconButton: {
    position: 'relative',
    padding: 4,
  },
  unreadDot: {
    position: 'absolute',
    top: 4,
    right: 4,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#EF4444',
    borderWidth: 1.5,
    borderColor: '#FFFFFF',
  },
  avatarButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    overflow: 'hidden',
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
  },
  avatar: {
    width: '100%',
    height: '100%',
  },
});
