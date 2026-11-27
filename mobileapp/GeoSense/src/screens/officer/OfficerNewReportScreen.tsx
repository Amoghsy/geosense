import { SafeAreaView } from 'react-native-safe-area-context';
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  TextInput,
  Alert,
} from 'react-native';
import { Feather, Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { HeaderBar } from '@/components/HeaderBar';
import { useApp } from '@/context/AppContext';
import { geoSenseApi } from '@/services/api';

export function OfficerNewReportScreen() {
  const { navigate, selectedLocation, currentUser } = useApp();
  const [severity, setSeverity] = useState<'Low' | 'Moderate' | 'High'>('High');
  const [incidentType, setIncidentType] = useState('Landslide / Rockfall');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!description.trim()) {
      Alert.alert('Missing Description', 'Please enter field observations before submitting.');
      return;
    }
    setSubmitting(true);
    try {
      const res = await geoSenseApi.submitInspection({
        latitude: selectedLocation.latitude,
        longitude: selectedLocation.longitude,
        location_name: selectedLocation.name,
        state: currentUser?.assigned_state || 'Meghalaya',
        district: currentUser?.assigned_district || 'East Khasi Hills',
        observations: `[${incidentType} | Severity: ${severity}] ${description.trim()}`,
        status: 'COMPLETED',
        follow_up_required: severity === 'High',
      });
      Alert.alert(
        'Inspection Logged',
        `Field inspection ${res.inspection_id} saved to GeoSense backend.`,
        [{ text: 'Done', onPress: () => navigate('officer-home') }]
      );
    } catch (err: any) {
      Alert.alert('Submission Failed', err?.message || 'Unable to submit inspection.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['left', 'right']}>
      <HeaderBar
        title="New Field Report"
        subtitle="SOHRA SLOPE · S1"
        variant="officer-dark"
        rightAction={
          <TouchableOpacity hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
            <Feather name="edit" size={20} color="#FFFFFF" />
          </TouchableOpacity>
        }
      />

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}>
        
        {/* Evidence Header */}
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionTitle}>Capture evidence</Text>
          <Text style={styles.attachmentCount}>1 attachment</Text>
        </View>

        {/* Evidence Grid: Photo + Upload Box */}
        <View style={styles.evidenceGrid}>
          <View style={styles.evidenceThumbCard}>
            <Image
              source={require('@/assets/images/design/field_report_photo.jpg')}
              style={styles.thumbImage}
              resizeMode="cover"
            />
            <View style={styles.thumbPill}>
              <Feather name="camera" size={10} color="#FFFFFF" />
              <Text style={styles.thumbPillText}>09:38 • GPS tagged</Text>
            </View>
          </View>

          <TouchableOpacity style={styles.uploadBox} activeOpacity={0.75}>
            <Feather name="camera" size={24} color="#00875A" />
            <Text style={styles.uploadTitle}>Photo / video</Text>
            <View style={styles.gallerySubRow}>
              <Feather name="image" size={12} color="#00875A" />
              <Text style={styles.gallerySubText}>Upload from gallery</Text>
            </View>
          </TouchableOpacity>
        </View>

        {/* Incident Type */}
        <Text style={styles.fieldLabel}>Incident type *</Text>
        <TouchableOpacity style={styles.dropdownBox} activeOpacity={0.8}>
          <Text style={styles.dropdownText}>{incidentType}</Text>
          <Feather name="chevron-down" size={18} color="#64748B" />
        </TouchableOpacity>

        {/* Severity Options */}
        <Text style={styles.fieldLabel}>Severity *</Text>
        <View style={styles.severityRow}>
          <TouchableOpacity
            style={[styles.severityPill, severity === 'Low' && styles.severityPillActive]}
            onPress={() => setSeverity('Low')}>
            <Text style={[styles.severityPillText, severity === 'Low' && styles.severityPillTextActive]}>
              Low
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.severityPill, severity === 'Moderate' && styles.severityPillActiveOrange]}
            onPress={() => setSeverity('Moderate')}>
            <Text
              style={[
                styles.severityPillText,
                severity === 'Moderate' && styles.severityPillTextActiveOrange,
              ]}>
              Moderate
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.severityPill, severity === 'High' && styles.severityPillActiveRed]}
            onPress={() => setSeverity('High')}>
            <Feather name="check" size={14} color="#FFFFFF" style={{ marginRight: 4 }} />
            <Text style={[styles.severityPillText, severity === 'High' && styles.severityPillTextActiveRed]}>
              High
            </Text>
          </TouchableOpacity>
        </View>

        {/* GPS Coordinates Box */}
        <View style={styles.coordsHeaderRow}>
          <Text style={styles.fieldLabel}>GPS coordinates</Text>
          <Text style={styles.accurateBadge}>Accurate to ±4 m</Text>
        </View>

        <View style={styles.coordsCard}>
          <View style={styles.coordsPinBox}>
            <Ionicons name="location-outline" size={22} color="#00875A" />
          </View>
          <View style={styles.coordsInfo}>
            <Text style={styles.coordsNumbers}>
              {selectedLocation.latitude.toFixed(4)}° N, {selectedLocation.longitude.toFixed(4)}° E
            </Text>
            <Text style={styles.coordsPlace}>{selectedLocation.name}</Text>
          </View>
          <TouchableOpacity style={styles.locateBtn}>
            <Feather name="crosshair" size={20} color="#00875A" />
          </TouchableOpacity>
        </View>

        {/* Description textarea */}
        <Text style={styles.fieldLabel}>Description *</Text>
        <TextInput
          style={styles.textArea}
          multiline
          numberOfLines={4}
          value={description}
          onChangeText={setDescription}
          textAlignVertical="top"
        />

        {/* Submit Report Button */}
        <TouchableOpacity
          style={styles.submitBtn}
          onPress={handleSubmit}
          activeOpacity={0.85}>
          <Feather name="send" size={18} color="#FFFFFF" />
          <Text style={styles.submitBtnText}>Submit report</Text>
        </TouchableOpacity>

        {/* Storage notice */}
        <View style={styles.draftSavedRow}>
          <Feather name="save" size={12} color="#64748B" />
          <Text style={styles.draftSavedText}>
            Draft saved locally • Evidence is securely stored
          </Text>
        </View>

      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#0D5C3A',
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
  sectionHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#0F172A',
  },
  attachmentCount: {
    fontSize: 12,
    fontWeight: '600',
    color: '#00875A',
  },
  evidenceGrid: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 20,
  },
  evidenceThumbCard: {
    flex: 1,
    height: 120,
    borderRadius: 16,
    overflow: 'hidden',
    position: 'relative',
  },
  thumbImage: {
    width: '100%',
    height: '100%',
  },
  thumbPill: {
    position: 'absolute',
    bottom: 8,
    left: 8,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(15, 23, 42, 0.75)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
    gap: 4,
  },
  thumbPillText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '700',
  },
  uploadBox: {
    flex: 1,
    height: 120,
    borderRadius: 16,
    backgroundColor: '#ECFDF5',
    borderWidth: 1.5,
    borderStyle: 'dashed',
    borderColor: '#A7F3D0',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 8,
  },
  uploadTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0F172A',
    marginTop: 6,
  },
  gallerySubRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 4,
  },
  gallerySubText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#00875A',
  },
  fieldLabel: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 8,
    marginTop: 6,
  },
  dropdownBox: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 14,
    height: 50,
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  dropdownText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#0F172A',
  },
  severityRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 16,
  },
  severityPill: {
    flex: 1,
    height: 44,
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  severityPillActive: {
    borderColor: '#00875A',
    backgroundColor: '#E8F5E9',
  },
  severityPillActiveOrange: {
    borderColor: '#F59E0B',
    backgroundColor: '#FEF3C7',
  },
  severityPillActiveRed: {
    borderColor: '#DC2626',
    backgroundColor: '#DC2626',
  },
  severityPillText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#64748B',
  },
  severityPillTextActive: {
    color: '#00875A',
    fontWeight: '700',
  },
  severityPillTextActiveOrange: {
    color: '#B45309',
    fontWeight: '700',
  },
  severityPillTextActiveRed: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  coordsHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  accurateBadge: {
    fontSize: 11,
    fontWeight: '700',
    color: '#00875A',
  },
  coordsCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ECFDF5',
    borderWidth: 1,
    borderColor: '#A7F3D0',
    borderRadius: 16,
    padding: 14,
    gap: 12,
    marginBottom: 16,
  },
  coordsPinBox: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  coordsInfo: {
    flex: 1,
  },
  coordsNumbers: {
    fontSize: 14,
    fontWeight: '800',
    color: '#0F172A',
  },
  coordsPlace: {
    fontSize: 11,
    color: '#065F46',
    marginTop: 2,
  },
  locateBtn: {
    padding: 6,
  },
  textArea: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 14,
    padding: 14,
    fontSize: 14,
    color: '#0F172A',
    minHeight: 100,
    marginBottom: 22,
    lineHeight: 20,
  },
  submitBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#00875A',
    borderRadius: 16,
    height: 52,
    gap: 8,
    shadowColor: '#00875A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 3,
    marginBottom: 12,
  },
  submitBtnText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  draftSavedRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  draftSavedText: {
    fontSize: 11,
    color: '#64748B',
  },
});

