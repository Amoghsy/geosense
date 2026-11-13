import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  ImageBackground,
  TextInput,
  ScrollView,
  Platform,
} from 'react-native';
import { Feather, Ionicons } from '@expo/vector-icons';
import { GeoSenseLogo } from '@/components/GeoSenseLogo';
import { useApp } from '@/context/AppContext';

export function OfficerLoginScreen() {
  const { loginOfficer, goBack } = useApp();
  const [officerId, setOfficerId] = useState('FO-1027');
  const [password, setPassword] = useState('password123');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);

  return (
    <View style={styles.container}>
      <ImageBackground
        source={require('@/assets/images/design/officer_hero_bg.jpg')}
        style={styles.heroBg}
        resizeMode="cover">
        
        {/* Dark Emerald Gradient Overlay */}
        <View style={styles.overlay} />

        <SafeAreaView style={styles.safeArea}>
          {/* Top Header with Back button and GeoSense Logo */}
          <View style={styles.headerRow}>
            <View style={styles.logoGroup}>
              <GeoSenseLogo size={28} textSize={22} color="#10B981" textColor="#FFFFFF" />
              <View style={styles.appBadge}>
                <Text style={styles.appBadgeText}>— FIELD OFFICER APP</Text>
              </View>
            </View>

            <TouchableOpacity
              onPress={goBack}
              style={styles.citizenBackBtn}
              activeOpacity={0.7}>
              <Text style={styles.citizenBackText}>Citizen Mode</Text>
            </TouchableOpacity>
          </View>

          {/* Hero Typography */}
          <View style={styles.heroTextSection}>
            <Text style={styles.heroTitle}>
              On the ground.{'\n'}Ahead of the risk.
            </Text>
            <Text style={styles.heroLocation}>KHASI HILLS / MEGHALAYA</Text>
          </View>

          {/* Login Bottom Sheet Card */}
          <View style={styles.loginSheet}>
            <View style={styles.sheetHeader}>
              <View style={styles.sheetTitleRow}>
                <Feather name="shield" size={20} color="#00875A" />
                <Text style={styles.sheetTitle}>Field officer login</Text>
              </View>
              <Text style={styles.sheetSubtitle}>
                Sign in to your secure operations workspace.
              </Text>
            </View>

            {/* Officer ID Input */}
            <Text style={styles.inputLabel}>Officer ID</Text>
            <View style={styles.inputContainer}>
              <Feather name="user" size={18} color="#64748B" style={styles.inputIcon} />
              <TextInput
                style={styles.textInput}
                value={officerId}
                onChangeText={setOfficerId}
                placeholder="FO-XXXX"
                placeholderTextColor="#94A3B8"
                autoCapitalize="characters"
              />
            </View>

            {/* Password Input */}
            <Text style={styles.inputLabel}>Password</Text>
            <View style={styles.inputContainer}>
              <Feather name="lock" size={18} color="#64748B" style={styles.inputIcon} />
              <TextInput
                style={styles.textInput}
                value={password}
                onChangeText={setPassword}
                secureTextEntry={!showPassword}
                placeholder="••••••••••••"
                placeholderTextColor="#94A3B8"
              />
              <TouchableOpacity
                onPress={() => setShowPassword(!showPassword)}
                style={styles.eyeBtn}>
                <Feather
                  name={showPassword ? 'eye-off' : 'eye'}
                  size={18}
                  color="#64748B"
                />
              </TouchableOpacity>
            </View>

            {/* Remember Me and Forgot Password */}
            <View style={styles.optionsRow}>
              <TouchableOpacity
                style={styles.rememberRow}
                onPress={() => setRememberMe(!rememberMe)}
                activeOpacity={0.7}>
                <View style={[styles.checkbox, rememberMe && styles.checkboxActive]}>
                  {rememberMe && <Feather name="check" size={12} color="#FFFFFF" />}
                </View>
                <Text style={styles.rememberText}>Remember my ID</Text>
              </TouchableOpacity>

              <TouchableOpacity activeOpacity={0.7}>
                <Text style={styles.forgotText}>Forgot Password?</Text>
              </TouchableOpacity>
            </View>

            {/* Secure Login Button */}
            <TouchableOpacity
              style={styles.loginBtn}
              onPress={loginOfficer}
              activeOpacity={0.85}>
              <Feather name="arrow-right" size={18} color="#FFFFFF" />
              <Text style={styles.loginBtnText}>Secure login</Text>
            </TouchableOpacity>

            {/* Encrypted Access Note */}
            <View style={styles.encryptedNoteRow}>
              <Feather name="lock" size={12} color="#64748B" />
              <Text style={styles.encryptedNoteText}>
                Authorized personnel only • Encrypted access
              </Text>
            </View>

            {/* Authority Footer */}
            <Text style={styles.authorityFooter}>
              Meghalaya State Disaster Management Authority
            </Text>
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
  heroBg: {
    flex: 1,
  },
  overlay: {
    ...StyleSheet.absoluteFill as object,
    backgroundColor: 'rgba(6, 78, 59, 0.45)',
  },
  safeArea: {
    flex: 1,
    justifyContent: 'space-between',
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 12,
  },
  logoGroup: {
    gap: 2,
  },
  appBadge: {
    marginTop: 2,
  },
  appBadgeText: {
    color: '#A7F3D0',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1.5,
  },
  citizenBackBtn: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 14,
  },
  citizenBackText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
  },
  heroTextSection: {
    paddingHorizontal: 24,
    marginBottom: 20,
  },
  heroTitle: {
    fontSize: 32,
    fontWeight: '900',
    color: '#FFFFFF',
    lineHeight: 40,
    letterSpacing: -0.5,
  },
  heroLocation: {
    fontSize: 12,
    fontWeight: '700',
    color: '#A7F3D0',
    letterSpacing: 1.5,
    marginTop: 10,
  },
  loginSheet: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    paddingHorizontal: 24,
    paddingTop: 24,
    paddingBottom: Platform.OS === 'ios' ? 24 : 18,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 8,
  },
  sheetHeader: {
    marginBottom: 16,
  },
  sheetTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 4,
  },
  sheetTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#0F172A',
  },
  sheetSubtitle: {
    fontSize: 13,
    color: '#64748B',
  },
  inputLabel: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 6,
    marginTop: 4,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
    borderRadius: 14,
    height: 48,
    paddingHorizontal: 14,
    marginBottom: 12,
  },
  inputIcon: {
    marginRight: 10,
  },
  textInput: {
    flex: 1,
    fontSize: 14,
    fontWeight: '600',
    color: '#0F172A',
  },
  eyeBtn: {
    padding: 6,
  },
  optionsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 18,
    marginTop: 2,
  },
  rememberRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  checkbox: {
    width: 18,
    height: 18,
    borderRadius: 5,
    borderWidth: 1.5,
    borderColor: '#CBD5E1',
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkboxActive: {
    backgroundColor: '#00875A',
    borderColor: '#00875A',
  },
  rememberText: {
    fontSize: 13,
    color: '#475569',
    fontWeight: '500',
  },
  forgotText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#00875A',
  },
  loginBtn: {
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
    marginBottom: 14,
  },
  loginBtnText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  encryptedNoteRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginBottom: 8,
  },
  encryptedNoteText: {
    fontSize: 11,
    color: '#64748B',
    fontWeight: '500',
  },
  authorityFooter: {
    textAlign: 'center',
    fontSize: 10,
    color: '#94A3B8',
    fontWeight: '500',
  },
});
