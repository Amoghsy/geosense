import { GeoSenseLogo } from '@/components/GeoSenseLogo';
import { useApp } from '@/context/AppContext';
import { Feather, Ionicons } from '@expo/vector-icons';
import { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import {
  ActivityIndicator,
  Image,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StatusBar as RNStatusBar,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';

export function LoginPortalScreen() {
  const {
    portalTab,
    setPortalTab,
    loginCitizen,
    registerCitizen,
    loginOfficer,
  } = useApp();

  const insets = useSafeAreaInsets();
  const topInset = Math.max(
    insets.top,
    Platform.OS === 'android' ? Math.max(RNStatusBar.currentHeight || 0, 46) : 44
  );
  const bottomInset = Math.max(insets.bottom, 24);

  // Citizen Auth mode: 'login' | 'register'
  const [citizenMode, setCitizenMode] = useState<'login' | 'register'>('login');
  const [citizenIdentifier, setCitizenIdentifier] = useState('aiban@geosense.in');
  const [citizenName, setCitizenName] = useState('');
  const [citizenEmail, setCitizenEmail] = useState('');
  const [citizenPhone, setCitizenPhone] = useState('');
  const [citizenPassword, setCitizenPassword] = useState('password123');
  const [showCitizenPassword, setShowCitizenPassword] = useState(false);

  // Officer Form state
  const [officerId, setOfficerId] = useState('FO-1027');
  const [password, setPassword] = useState('password123');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  const handleCitizenSubmit = async () => {
    setAuthError(null);
    setIsSubmitting(true);
    try {
      if (citizenMode === 'login') {
        if (!citizenIdentifier.trim() || !citizenPassword) {
          throw new Error('Please enter your email/phone and password.');
        }
        await loginCitizen(citizenIdentifier, citizenPassword);
      } else {
        if (!citizenName.trim() || !citizenEmail.trim() || citizenPassword.length < 6) {
          throw new Error('Enter your full name, valid email, and a password (min 6 chars).');
        }
        await registerCitizen(citizenName, citizenEmail, citizenPhone, citizenPassword);
      }
    } catch (err: any) {
      setAuthError(err?.message || 'Authentication failed. Check your connection.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOfficerSubmit = async () => {
    setAuthError(null);
    setIsSubmitting(true);
    try {
      if (!officerId.trim() || !password) {
        throw new Error('Please enter your Officer ID / Email and password.');
      }
      await loginOfficer(officerId, password);
    } catch (err: any) {
      setAuthError(err?.message || 'Officer login failed. Check your credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const selectOfficerPreset = (presetId: string) => {
    setAuthError(null);
    setOfficerId(presetId);
    setPassword('password123');
  };

  return (
    <View style={styles.container}>
      <StatusBar style="light" />
      {/* Background Image */}
      <Image
        source={require('@/assets/images/design/officer_hero_bg.jpg')}
        style={styles.heroBgImage}
        resizeMode="cover"
      />

      {/* Dark Emerald / Forest Gradient Overlay */}
      <View style={styles.overlay} />

      <SafeAreaView style={styles.safeArea}>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          style={styles.keyboardAvoid}>
          <ScrollView
            contentContainerStyle={[
              styles.scrollContent,
              { paddingTop: topInset + 8, paddingBottom: bottomInset + 20 },
            ]}
            showsVerticalScrollIndicator={false}
            keyboardShouldPersistTaps="handled">

            {/* Top Government Authority Bar */}
            <View style={styles.govBar}>
              <View style={styles.govEmblemBox}>
                <Feather name="shield" size={13} color="#10B981" />
              </View>
              <View style={styles.govTextCol}>
                <Text style={styles.govTitle}>GOVERNMENT OF MEGHALAYA</Text>
                <Text style={styles.govSubtitle}>State Disaster Management Authority (SDMA)</Text>
              </View>
              <View style={styles.statusLivePill}>
                <View style={styles.pulseDot} />
                <Text style={styles.statusLiveText}>GRID LIVE</Text>
              </View>
            </View>

            {/* GeoSense Main Brand Header */}
            <View style={styles.brandHeader}>
              <GeoSenseLogo size={34} textSize={26} color="#10B981" textColor="#FFFFFF" />
              <Text style={styles.systemTagline}>
                AI Geological Hazard & Early Warning System
              </Text>
            </View>

            {/* Segmented Dual Portal Switcher */}
            <View style={styles.portalSwitchWrapper}>
              <TouchableOpacity
                style={[
                  styles.portalTab,
                  portalTab === 'citizen' && styles.portalTabActive,
                ]}
                onPress={() => setPortalTab('citizen')}
                activeOpacity={0.85}>
                <Ionicons
                  name={portalTab === 'citizen' ? 'people' : 'people-outline'}
                  size={18}
                  color={portalTab === 'citizen' ? '#064E3B' : '#94A3B8'}
                />
                <Text
                  style={[
                    styles.portalTabText,
                    portalTab === 'citizen' && styles.portalTabTextActive,
                  ]}>
                  Citizen Portal
                </Text>
                {portalTab === 'citizen' && <View style={styles.activeDot} />}
              </TouchableOpacity>

              <TouchableOpacity
                style={[
                  styles.portalTab,
                  portalTab === 'officer' && styles.portalTabActive,
                ]}
                onPress={() => setPortalTab('officer')}
                activeOpacity={0.85}>
                <Feather
                  name="shield"
                  size={17}
                  color={portalTab === 'officer' ? '#064E3B' : '#94A3B8'}
                />
                <Text
                  style={[
                    styles.portalTabText,
                    portalTab === 'officer' && styles.portalTabTextActive,
                  ]}>
                  Field Officer
                </Text>
                {portalTab === 'officer' && <View style={styles.activeDot} />}
              </TouchableOpacity>
            </View>

            {/* ===================== CITIZEN PORTAL ===================== */}
            {portalTab === 'citizen' && (
              <View style={styles.portalCard}>
                {/* Card Header & Badge */}
                <View style={styles.cardHeader}>
                  <View style={styles.badgeRow}>
                    <View style={styles.publicBadge}>
                      <Feather name="users" size={12} color="#00875A" />
                      <Text style={styles.publicBadgeText}>PUBLIC SAFETY PORTAL</Text>
                    </View>
                    <View style={styles.regionBadge}>
                      <Feather name="map-pin" size={12} color="#64748B" />
                      <Text style={styles.regionBadgeText}>Cherrapunji & Khasi Hills</Text>
                    </View>
                  </View>

                  <Text style={styles.cardTitle}>Stay Alert. Stay Safe.</Text>
                  <Text style={styles.cardSubtitle}>
                    Sign in or register for live landslide probability, evacuation corridors, and community reporting.
                  </Text>
                </View>

                {/* Sign In / Register Switch */}
                <View style={{ flexDirection: 'row', backgroundColor: '#F1F5F9', borderRadius: 10, padding: 4, marginBottom: 14 }}>
                  <TouchableOpacity
                    style={{
                      flex: 1,
                      paddingVertical: 8,
                      borderRadius: 8,
                      alignItems: 'center',
                      backgroundColor: citizenMode === 'login' ? '#FFFFFF' : 'transparent',
                    }}
                    onPress={() => { setCitizenMode('login'); setAuthError(null); }}>
                    <Text style={{ fontSize: 13, fontWeight: '700', color: citizenMode === 'login' ? '#064E3B' : '#64748B' }}>
                      Sign In
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={{
                      flex: 1,
                      paddingVertical: 8,
                      borderRadius: 8,
                      alignItems: 'center',
                      backgroundColor: citizenMode === 'register' ? '#FFFFFF' : 'transparent',
                    }}
                    onPress={() => { setCitizenMode('register'); setAuthError(null); }}>
                    <Text style={{ fontSize: 13, fontWeight: '700', color: citizenMode === 'register' ? '#064E3B' : '#64748B' }}>
                      Create Account
                    </Text>
                  </TouchableOpacity>
                </View>

                {authError && (
                  <View style={{ backgroundColor: '#FEE2E2', borderRadius: 10, padding: 10, marginBottom: 12, flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                    <Feather name="alert-circle" size={16} color="#DC2626" />
                    <Text style={{ color: '#B91C1C', fontSize: 12, fontWeight: '600', flex: 1 }}>{authError}</Text>
                  </View>
                )}

                {citizenMode === 'login' ? (
                  <>
                    <View style={styles.inputGroup}>
                      <Text style={styles.fieldLabel}>Email or Mobile Number</Text>
                      <View style={styles.inputContainer}>
                        <Feather name="mail" size={18} color="#64748B" style={styles.fieldIcon} />
                        <TextInput
                          style={styles.textInput}
                          value={citizenIdentifier}
                          onChangeText={setCitizenIdentifier}
                          placeholder="aiban@geosense.in"
                          placeholderTextColor="#94A3B8"
                          autoCapitalize="none"
                          keyboardType="email-address"
                        />
                      </View>
                    </View>

                    <View style={styles.inputGroup}>
                      <Text style={styles.fieldLabel}>Password</Text>
                      <View style={styles.inputContainer}>
                        <Feather name="lock" size={18} color="#64748B" style={styles.fieldIcon} />
                        <TextInput
                          style={styles.textInput}
                          value={citizenPassword}
                          onChangeText={setCitizenPassword}
                          secureTextEntry={!showCitizenPassword}
                          placeholder="••••••••"
                          placeholderTextColor="#94A3B8"
                        />
                        <TouchableOpacity
                          onPress={() => setShowCitizenPassword(!showCitizenPassword)}
                          style={styles.eyeBtn}>
                          <Feather name={showCitizenPassword ? 'eye-off' : 'eye'} size={18} color="#64748B" />
                        </TouchableOpacity>
                      </View>
                    </View>
                  </>
                ) : (
                  <>
                    <View style={styles.inputGroup}>
                      <Text style={styles.fieldLabel}>Full Name *</Text>
                      <View style={styles.inputContainer}>
                        <Feather name="user" size={18} color="#64748B" style={styles.fieldIcon} />
                        <TextInput
                          style={styles.textInput}
                          value={citizenName}
                          onChangeText={setCitizenName}
                          placeholder="e.g. Aiban Khonglah"
                          placeholderTextColor="#94A3B8"
                        />
                      </View>
                    </View>

                    <View style={styles.inputGroup}>
                      <Text style={styles.fieldLabel}>Email Address *</Text>
                      <View style={styles.inputContainer}>
                        <Feather name="mail" size={18} color="#64748B" style={styles.fieldIcon} />
                        <TextInput
                          style={styles.textInput}
                          value={citizenEmail}
                          onChangeText={setCitizenEmail}
                          placeholder="you@example.com"
                          placeholderTextColor="#94A3B8"
                          autoCapitalize="none"
                          keyboardType="email-address"
                        />
                      </View>
                    </View>

                    <View style={styles.inputGroup}>
                      <Text style={styles.fieldLabel}>Mobile Number</Text>
                      <View style={styles.inputContainer}>
                        <Feather name="phone" size={18} color="#64748B" style={styles.fieldIcon} />
                        <TextInput
                          style={styles.textInput}
                          value={citizenPhone}
                          onChangeText={setCitizenPhone}
                          placeholder="+91 98630 01482"
                          placeholderTextColor="#94A3B8"
                          keyboardType="phone-pad"
                        />
                      </View>
                    </View>

                    <View style={styles.inputGroup}>
                      <Text style={styles.fieldLabel}>Password * (min 6 chars)</Text>
                      <View style={styles.inputContainer}>
                        <Feather name="lock" size={18} color="#64748B" style={styles.fieldIcon} />
                        <TextInput
                          style={styles.textInput}
                          value={citizenPassword}
                          onChangeText={setCitizenPassword}
                          secureTextEntry={!showCitizenPassword}
                          placeholder="Create password"
                          placeholderTextColor="#94A3B8"
                        />
                        <TouchableOpacity
                          onPress={() => setShowCitizenPassword(!showCitizenPassword)}
                          style={styles.eyeBtn}>
                          <Feather name={showCitizenPassword ? 'eye-off' : 'eye'} size={18} color="#64748B" />
                        </TouchableOpacity>
                      </View>
                    </View>
                  </>
                )}

                {/* Primary Citizen Login Button */}
                <TouchableOpacity
                  style={[styles.citizenPrimaryBtn, isSubmitting && { opacity: 0.7 }]}
                  onPress={handleCitizenSubmit}
                  disabled={isSubmitting}
                  activeOpacity={0.85}>
                  {isSubmitting ? (
                    <ActivityIndicator color="#FFFFFF" size="small" />
                  ) : (
                    <>
                      <Text style={styles.citizenPrimaryBtnText}>
                        {citizenMode === 'login' ? 'Sign In to Citizen Portal' : 'Create Account & Continue'}
                      </Text>
                      <Feather name="arrow-right" size={19} color="#FFFFFF" />
                    </>
                  )}
                </TouchableOpacity>

                {/* Quick Feature Chips */}
                <View style={styles.featuresPreview}>
                  <View style={styles.featureChip}>
                    <Feather name="alert-triangle" size={13} color="#EF4444" />
                    <Text style={styles.featureChipText}>87% Peak Risk Warning</Text>
                  </View>
                  <View style={styles.featureChip}>
                    <Feather name="navigation" size={13} color="#00875A" />
                    <Text style={styles.featureChipText}>Live Evacuation Routes</Text>
                  </View>
                  <View style={styles.featureChip}>
                    <Feather name="shield" size={13} color="#2563EB" />
                    <Text style={styles.featureChipText}>Slope Hazard Assessment</Text>
                  </View>
                </View>

                {/* Emergency Helplines Notice */}
                <View style={styles.emergencyNoteBox}>
                  <Feather name="phone-call" size={13} color="#065F46" />
                  <Text style={styles.emergencyNoteText}>
                    24/7 State Disaster Helpline: <Text style={styles.boldText}>1070</Text> • Ambulance: <Text style={styles.boldText}>108</Text>
                  </Text>
                </View>
              </View>
            )}

            {/* ===================== FIELD OFFICER PORTAL ===================== */}
            {portalTab === 'officer' && (
              <View style={styles.portalCard}>
                {/* Card Header & Badge */}
                <View style={styles.cardHeader}>
                  <View style={styles.badgeRow}>
                    <View style={styles.officerBadge}>
                      <Feather name="lock" size={12} color="#0D5C3A" />
                      <Text style={styles.officerBadgeText}>RESTRICTED OPERATIONS</Text>
                    </View>
                    <View style={styles.regionBadge}>
                      <Feather name="shield" size={12} color="#64748B" />
                      <Text style={styles.regionBadgeText}>Tactical Node • Khasi Hills</Text>
                    </View>
                  </View>

                  <Text style={styles.cardTitle}>Field Officer Portal</Text>
                  <Text style={styles.cardSubtitle}>
                    Sign in to your tactical sensor telemetry, site inspections & incident verification workspace.
                  </Text>
                </View>

                {/* Officer ID Input */}
                <View style={styles.inputGroup}>
                  <Text style={styles.fieldLabel}>Officer ID</Text>
                  <View style={styles.inputContainer}>
                    <Feather name="user-check" size={18} color="#64748B" style={styles.fieldIcon} />
                    <TextInput
                      style={styles.textInput}
                      value={officerId}
                      onChangeText={setOfficerId}
                      placeholder="FO-1027"
                      placeholderTextColor="#94A3B8"
                      autoCapitalize="characters"
                    />
                  </View>
                </View>

                {/* Password Input */}
                <View style={styles.inputGroup}>
                  <Text style={styles.fieldLabel}>Password</Text>
                  <View style={styles.inputContainer}>
                    <Feather name="lock" size={18} color="#64748B" style={styles.fieldIcon} />
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
                    <Text style={styles.rememberText}>Remember ID</Text>
                  </TouchableOpacity>

                  <TouchableOpacity activeOpacity={0.7}>
                    <Text style={styles.forgotText}>Forgot password?</Text>
                  </TouchableOpacity>
                </View>

                {/* Quick Select Presets for Field Officers */}
                <View style={styles.presetsContainer}>
                  <Text style={styles.presetsLabel}>Quick officer sign-in:</Text>
                  <View style={styles.presetButtonsRow}>
                    <TouchableOpacity
                      style={[
                        styles.presetBtn,
                        officerId === 'FO-1027' && styles.presetBtnActive,
                      ]}
                      onPress={() => selectOfficerPreset('FO-1027')}
                      activeOpacity={0.7}>
                      <Text
                        style={[
                          styles.presetBtnText,
                          officerId === 'FO-1027' && styles.presetBtnTextActive,
                        ]}>
                        FO-1027 (Cherrapunji)
                      </Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[
                        styles.presetBtn,
                        officerId === 'FO-2048' && styles.presetBtnActive,
                      ]}
                      onPress={() => selectOfficerPreset('FO-2048')}
                      activeOpacity={0.7}>
                      <Text
                        style={[
                          styles.presetBtnText,
                          officerId === 'FO-2048' && styles.presetBtnTextActive,
                        ]}>
                        FO-2048 (Mawsynram)
                      </Text>
                    </TouchableOpacity>
                  </View>
                </View>

                {authError && portalTab === 'officer' && (
                  <View style={{ backgroundColor: '#FEE2E2', borderRadius: 10, padding: 10, marginBottom: 12, flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                    <Feather name="alert-circle" size={16} color="#DC2626" />
                    <Text style={{ color: '#B91C1C', fontSize: 12, fontWeight: '600', flex: 1 }}>{authError}</Text>
                  </View>
                )}

                {/* Primary Officer Login Button */}
                <TouchableOpacity
                  style={[styles.officerPrimaryBtn, isSubmitting && { opacity: 0.7 }]}
                  onPress={handleOfficerSubmit}
                  disabled={isSubmitting}
                  activeOpacity={0.85}>
                  {isSubmitting ? (
                    <ActivityIndicator color="#FFFFFF" size="small" />
                  ) : (
                    <>
                      <Feather name="shield" size={18} color="#FFFFFF" />
                      <Text style={styles.officerPrimaryBtnText}>Secure Login to Ops</Text>
                      <Feather name="arrow-right" size={19} color="#FFFFFF" />
                    </>
                  )}
                </TouchableOpacity>

                {/* Security Note */}
                <View style={styles.securityNoteRow}>
                  <Feather name="lock" size={12} color="#64748B" />
                  <Text style={styles.securityNoteText}>
                    Authorized personnel only • 256-bit encrypted operational tunnel
                  </Text>
                </View>
              </View>
            )}

            {/* System Telemetry & Footer */}
            <View style={styles.footerContainer}>
              <View style={styles.telemetryRow}>
                <View style={styles.telemetryItem}>
                  <View style={[styles.sensorDot, { backgroundColor: '#10B981' }]} />
                  <Text style={styles.telemetryText}>14 Geotechnical Sensors Online</Text>
                </View>
                <Text style={styles.telemetryDivider}>•</Text>
                <View style={styles.telemetryItem}>
                  <View style={[styles.sensorDot, { backgroundColor: '#38BDF8' }]} />
                  <Text style={styles.telemetryText}>Doppler Radar Synced</Text>
                </View>
              </View>
              <Text style={styles.footerCopyright}>
                Meghalaya State Disaster Management Authority • GeoSense v1.0
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
    backgroundColor: '#06130D',
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
    backgroundColor: 'rgba(5, 20, 14, 0.82)',
  },
  safeArea: {
    flex: 1,
  },
  keyboardAvoid: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 40,
    maxWidth: 500,
    width: '100%',
    alignSelf: 'center',
  },

  // Gov Bar
  govBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(15, 23, 42, 0.65)',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    marginBottom: 16,
  },
  govEmblemBox: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: 'rgba(16, 185, 129, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
  },
  govTextCol: {
    flex: 1,
  },
  govTitle: {
    fontSize: 10,
    fontWeight: '800',
    color: '#E2E8F0',
    letterSpacing: 0.6,
  },
  govSubtitle: {
    fontSize: 9,
    color: '#94A3B8',
    fontWeight: '500',
  },
  statusLivePill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(16, 185, 129, 0.2)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(16, 185, 129, 0.35)',
    gap: 4,
  },
  pulseDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#10B981',
  },
  statusLiveText: {
    fontSize: 9,
    fontWeight: '700',
    color: '#10B981',
    letterSpacing: 0.5,
  },

  // Brand Header
  brandHeader: {
    alignItems: 'center',
    marginVertical: 12,
  },
  systemTagline: {
    fontSize: 13,
    color: '#CBD5E1',
    fontWeight: '500',
    marginTop: 6,
    letterSpacing: -0.2,
    textAlign: 'center',
  },

  // Portal Switcher
  portalSwitchWrapper: {
    flexDirection: 'row',
    backgroundColor: 'rgba(15, 23, 42, 0.75)',
    padding: 4,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
    marginVertical: 14,
  },
  portalTab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderRadius: 12,
    gap: 8,
  },
  portalTabActive: {
    backgroundColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
  portalTabText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#94A3B8',
  },
  portalTabTextActive: {
    color: '#064E3B',
    fontWeight: '700',
  },
  activeDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    backgroundColor: '#00875A',
  },

  // Portal Main Card
  portalCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 22,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.25,
    shadowRadius: 16,
    elevation: 8,
  },
  cardHeader: {
    marginBottom: 18,
  },
  badgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
    flexWrap: 'wrap',
    gap: 6,
  },
  publicBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ECFDF5',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#A7F3D0',
    gap: 5,
  },
  publicBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#00875A',
    letterSpacing: 0.4,
  },
  officerBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ECFDF5',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#A7F3D0',
    gap: 5,
  },
  officerBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#0D5C3A',
    letterSpacing: 0.4,
  },
  regionBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F1F5F9',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    gap: 4,
  },
  regionBadgeText: {
    fontSize: 11,
    color: '#475569',
    fontWeight: '500',
  },
  cardTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: '#0F172A',
    letterSpacing: -0.5,
    marginBottom: 6,
  },
  cardSubtitle: {
    fontSize: 13,
    color: '#64748B',
    lineHeight: 19,
  },

  // Input Groups
  inputGroup: {
    marginBottom: 14,
  },
  fieldLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#334155',
    marginBottom: 6,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 14,
    paddingHorizontal: 14,
    height: 48,
  },
  fieldIcon: {
    marginRight: 10,
  },
  textInput: {
    flex: 1,
    fontSize: 14,
    color: '#0F172A',
    fontWeight: '500',
  },
  eyeBtn: {
    padding: 6,
  },

  // Options row
  optionsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
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
    backgroundColor: '#FFFFFF',
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
    color: '#00875A',
    fontWeight: '600',
  },

  // Buttons
  citizenPrimaryBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#00875A',
    borderRadius: 14,
    height: 50,
    marginTop: 6,
    marginBottom: 14,
    gap: 8,
    shadowColor: '#00875A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 3,
  },
  citizenPrimaryBtnText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FFFFFF',
  },

  officerPrimaryBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#0D5C3A',
    borderRadius: 14,
    height: 50,
    marginTop: 6,
    marginBottom: 12,
    gap: 8,
    shadowColor: '#0D5C3A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 3,
  },
  officerPrimaryBtnText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FFFFFF',
  },

  // Presets
  presetsContainer: {
    marginBottom: 16,
    paddingTop: 4,
  },
  presetsLabel: {
    fontSize: 11,
    color: '#64748B',
    fontWeight: '600',
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  presetButtonsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  presetBtn: {
    flex: 1,
    paddingVertical: 7,
    paddingHorizontal: 8,
    borderRadius: 8,
    backgroundColor: '#F1F5F9',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    alignItems: 'center',
  },
  presetBtnActive: {
    backgroundColor: '#ECFDF5',
    borderColor: '#10B981',
  },
  presetBtnText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#475569',
  },
  presetBtnTextActive: {
    color: '#065F46',
    fontWeight: '700',
  },

  // Features Preview
  featuresPreview: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginBottom: 12,
  },
  featureChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    paddingVertical: 5,
    paddingHorizontal: 9,
    borderRadius: 8,
    gap: 5,
  },
  featureChipText: {
    fontSize: 11,
    color: '#334155',
    fontWeight: '600',
  },

  // Notes
  emergencyNoteBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ECFDF5',
    borderRadius: 10,
    padding: 10,
    gap: 8,
  },
  emergencyNoteText: {
    fontSize: 11,
    color: '#065F46',
    flex: 1,
  },
  boldText: {
    fontWeight: '700',
  },
  securityNoteRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingTop: 4,
  },
  securityNoteText: {
    fontSize: 11,
    color: '#64748B',
    textAlign: 'center',
  },

  // Footer & Telemetry
  footerContainer: {
    alignItems: 'center',
    marginTop: 20,
    gap: 8,
  },
  telemetryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  telemetryItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  sensorDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  telemetryText: {
    fontSize: 11,
    color: '#94A3B8',
    fontWeight: '500',
  },
  telemetryDivider: {
    color: '#64748B',
    fontSize: 12,
  },
  footerCopyright: {
    fontSize: 11,
    color: '#64748B',
    textAlign: 'center',
    fontWeight: '500',
  },
});
