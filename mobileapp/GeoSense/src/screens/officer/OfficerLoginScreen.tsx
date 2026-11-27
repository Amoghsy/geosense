import React, { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  TextInput,
  Platform,
  StatusBar as RNStatusBar,
  ScrollView,
  KeyboardAvoidingView,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { Feather } from '@expo/vector-icons';
import { GeoSenseLogo } from '@/components/GeoSenseLogo';
import { useApp } from '@/context/AppContext';

export function OfficerLoginScreen() {
  const { loginOfficer, navigate, setPortalTab } = useApp();
  const insets = useSafeAreaInsets();
  const topInset = Math.max(
    insets.top,
    Platform.OS === 'android' ? Math.max(RNStatusBar.currentHeight || 0, 46) : 44
  );
  const bottomInset = Math.max(insets.bottom, Platform.OS === 'android' ? 16 : 12);

  const [officerId, setOfficerId] = useState('FO-1027');
  const [password, setPassword] = useState('password123');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  const handleLogin = async () => {
    setAuthError(null);
    setIsSubmitting(true);
    try {
      await loginOfficer(officerId, password);
    } catch (err: any) {
      setAuthError(err?.message || 'Officer authentication failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <View style={styles.container}>
      <StatusBar style="light" />
      {/* Background Image replacing deprecated ImageBackground */}
      <Image
        source={require('@/assets/images/design/officer_hero_bg.jpg')}
        style={styles.heroBgImage}
        resizeMode="cover"
      />

      {/* Dark Emerald Gradient Overlay */}
      <View style={styles.overlay} />

      <SafeAreaView style={styles.safeArea} edges={['left', 'right']}>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          style={styles.keyboardAvoid}>
          <ScrollView
            contentContainerStyle={styles.scrollContent}
            showsVerticalScrollIndicator={false}
            keyboardShouldPersistTaps="handled">
            
            {/* Top Header with Back button and GeoSense Logo */}
            <View style={[styles.headerRow, { paddingTop: topInset + 8 }]}>
              <View style={styles.logoGroup}>
                <GeoSenseLogo size={28} textSize={22} color="#10B981" textColor="#FFFFFF" />
                <View style={styles.appBadge}>
                  <Text style={styles.appBadgeText}>— FIELD OFFICER APP</Text>
                </View>
              </View>

              <TouchableOpacity
                onPress={() => {
                  setPortalTab('citizen');
                  navigate('login-portal');
                }}
                style={styles.citizenBackBtn}
                activeOpacity={0.7}>
                <Text style={styles.citizenBackText}>Citizen Portal</Text>
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
            <View style={[styles.loginSheet, { paddingBottom: bottomInset + 20 }]}>
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

              {authError && (
                <View style={{ backgroundColor: '#FEE2E2', borderRadius: 10, padding: 10, marginBottom: 12, flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                  <Feather name="alert-circle" size={16} color="#DC2626" />
                  <Text style={{ color: '#B91C1C', fontSize: 12, fontWeight: '600', flex: 1 }}>{authError}</Text>
                </View>
              )}

              {/* Secure Login Button */}
              <TouchableOpacity
                style={[styles.loginBtn, isSubmitting && { opacity: 0.7 }]}
                onPress={handleLogin}
                disabled={isSubmitting}
                activeOpacity={0.85}>
                {isSubmitting ? (
                  <ActivityIndicator color="#FFFFFF" size="small" />
                ) : (
                  <>
                    <Feather name="arrow-right" size={18} color="#FFFFFF" />
                    <Text style={styles.loginBtnText}>Secure login</Text>
                  </>
                )}
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
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
    position: 'relative',
  },
  heroBgImage: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    width: '100%',
    height: '100%',
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(6, 78, 59, 0.45)',
  },
  safeArea: {
    flex: 1,
  },
  keyboardAvoid: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'space-between',
    maxWidth: 500,
    width: '100%',
    alignSelf: 'center',
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 10,
  },
  logoGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  appBadge: {
    backgroundColor: 'rgba(16, 185, 129, 0.2)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  appBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#34D399',
    letterSpacing: 0.5,
  },
  citizenBackBtn: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.4)',
  },
  citizenBackText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  heroTextSection: {
    paddingHorizontal: 24,
    marginTop: 40,
    marginBottom: 30,
  },
  heroTitle: {
    fontSize: 34,
    fontWeight: '800',
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
    fontWeight: '700',
    color: '#0F172A',
    letterSpacing: -0.3,
  },
  sheetSubtitle: {
    fontSize: 13,
    color: '#64748B',
  },
  inputLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#334155',
    marginBottom: 6,
    marginTop: 10,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 12,
    paddingHorizontal: 12,
    height: 48,
  },
  inputIcon: {
    marginRight: 10,
  },
  textInput: {
    flex: 1,
    fontSize: 15,
    color: '#0F172A',
    fontWeight: '500',
  },
  eyeBtn: {
    padding: 6,
  },
  optionsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 14,
    marginBottom: 18,
  },
  rememberRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  checkbox: {
    width: 18,
    height: 18,
    borderRadius: 4,
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
    color: '#64748B',
  },
  forgotText: {
    fontSize: 13,
    color: '#00875A',
    fontWeight: '600',
  },
  loginBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#00875A',
    borderRadius: 14,
    height: 50,
    gap: 8,
    shadowColor: '#00875A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 3,
  },
  loginBtnText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  encryptedNoteRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 14,
  },
  encryptedNoteText: {
    fontSize: 11,
    color: '#64748B',
  },
  authorityFooter: {
    fontSize: 11,
    color: '#94A3B8',
    textAlign: 'center',
    marginTop: 10,
  },
});
