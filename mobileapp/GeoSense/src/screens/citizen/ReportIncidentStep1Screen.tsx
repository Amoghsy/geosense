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
} from 'react-native';
import { Feather, Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { HeaderBar } from '@/components/HeaderBar';
import { useApp } from '@/context/AppContext';

export function ReportIncidentStep1Screen() {
  const { navigate, incidentDraft, updateIncidentDraft } = useApp();
  const [description, setDescription] = useState(incidentDraft.description);

  const handleContinue = () => {
    updateIncidentDraft({ description });
    navigate('report-incident-2');
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['left', 'right']}>
      <HeaderBar
        title="Report a Landslide Incident"
        subtitle="Step 1 of 2 · Evidence & location"
        variant="sub-light"
      />

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}>
        
        {/* Safety Warning Card */}
        <View style={styles.warningBox}>
          <Ionicons name="shield-outline" size={18} color="#D97706" />
          <Text style={styles.warningText}>
            Only report from a safe place. For immediate danger, call 112.
          </Text>
        </View>

        {/* Incident Photos */}
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionTitle}>Incident photos</Text>
          <Text style={styles.attachmentCount}>1 of 5 attached</Text>
        </View>

        {/* Attached photo preview */}
        <View style={styles.photoPreviewCard}>
          <Image
            source={require('@/assets/images/design/landslide_photo.jpg')}
            style={styles.photoImage}
            resizeMode="cover"
          />
          <View style={styles.photoBadgeRow}>
            <View style={styles.gpsTagPill}>
              <Text style={styles.gpsTagText}>Photo 1 · GPS tagged</Text>
            </View>
            <TouchableOpacity style={styles.editPhotoBtn}>
              <Feather name="edit-2" size={14} color="#0F172A" />
            </TouchableOpacity>
          </View>
        </View>

        {/* Photo Action Buttons */}
        <View style={styles.photoActionsRow}>
          <TouchableOpacity style={styles.takePhotoBtn} activeOpacity={0.8}>
            <Feather name="camera" size={18} color="#00875A" />
            <Text style={styles.takePhotoText}>Take Photo</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.uploadBtn} activeOpacity={0.8}>
            <Feather name="upload" size={18} color="#334155" />
            <Text style={styles.uploadText}>Upload from Gallery</Text>
          </TouchableOpacity>
        </View>

        {/* Incident Type */}
        <Text style={styles.fieldLabel}>Incident Type</Text>
        <TouchableOpacity style={styles.dropdownField} activeOpacity={0.8}>
          <Text style={styles.dropdownValue}>{incidentDraft.type}</Text>
          <Feather name="chevron-down" size={18} color="#64748B" />
        </TouchableOpacity>

        {/* Location Box */}
        <View style={styles.locationCard}>
          <View style={styles.locationHeaderRow}>
            <Text style={styles.autoGpsLabel}>Auto GPS · {incidentDraft.location}</Text>
            <View style={styles.accuracyPill}>
              <View style={styles.greenDot} />
              <Text style={styles.accuracyText}>{incidentDraft.accuracy}</Text>
            </View>
          </View>
          <Text style={styles.coordsText}>{incidentDraft.coords}</Text>
          <TouchableOpacity style={styles.chooseManualRow} onPress={() => navigate('map')}>
            <Text style={styles.chooseManualText}>Choose location on map</Text>
            <Feather name="arrow-right" size={14} color="#00875A" />
          </TouchableOpacity>
        </View>

        {/* Description textarea */}
        <Text style={styles.fieldLabel}>Description</Text>
        <TextInput
          style={styles.textArea}
          placeholder="Describe what happened..."
          placeholderTextColor="#94A3B8"
          multiline
          numberOfLines={4}
          value={description}
          onChangeText={setDescription}
          textAlignVertical="top"
        />

        {/* Continue Button */}
        <TouchableOpacity
          style={styles.continueButton}
          onPress={handleContinue}
          activeOpacity={0.85}>
          <Text style={styles.continueButtonText}>Continue to incident details</Text>
          <Feather name="arrow-right" size={18} color="#FFFFFF" />
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
    paddingTop: 14,
    paddingBottom: 95,
  },
  warningBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEF3C7',
    borderWidth: 1,
    borderColor: '#FDE68A',
    borderRadius: 14,
    padding: 12,
    gap: 10,
    marginBottom: 20,
  },
  warningText: {
    fontSize: 12,
    color: '#92400E',
    fontWeight: '600',
    flex: 1,
    lineHeight: 18,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#0F172A',
  },
  attachmentCount: {
    fontSize: 13,
    color: '#64748B',
  },
  photoPreviewCard: {
    borderRadius: 18,
    overflow: 'hidden',
    position: 'relative',
    height: 180,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  photoImage: {
    width: '100%',
    height: '100%',
  },
  photoBadgeRow: {
    position: 'absolute',
    bottom: 12,
    left: 12,
    right: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  gpsTagPill: {
    backgroundColor: 'rgba(0,0,0,0.6)',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
  },
  gpsTagText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  editPhotoBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.15,
    shadowRadius: 3,
  },
  photoActionsRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 20,
  },
  takePhotoBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#E8F5E9',
    borderRadius: 14,
    height: 48,
    gap: 8,
  },
  takePhotoText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#00875A',
  },
  uploadBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F1F5F9',
    borderRadius: 14,
    height: 48,
    gap: 8,
  },
  uploadText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#334155',
  },
  fieldLabel: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 8,
    marginTop: 4,
  },
  dropdownField: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 14,
    height: 50,
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  dropdownValue: {
    fontSize: 15,
    color: '#0F172A',
    fontWeight: '500',
  },
  locationCard: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
  },
  locationHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  autoGpsLabel: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
  },
  accuracyPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#D1FAE5',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
    gap: 4,
  },
  greenDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#10B981',
  },
  accuracyText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#065F46',
  },
  coordsText: {
    fontSize: 13,
    color: '#64748B',
    marginTop: 4,
  },
  chooseManualRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 10,
  },
  chooseManualText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#00875A',
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
    marginBottom: 24,
  },
  continueButton: {
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
  },
  continueButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
});

