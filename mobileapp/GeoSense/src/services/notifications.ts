import { geoSenseApi } from './api';
import { ScreenName } from '@/context/AppContext';

/**
 * Firebase Cloud Messaging (FCM) & Expo Push registration helper.
 * Note: Native FCM background push requires an Expo Development Build with
 * @react-native-firebase/messaging + google-services.json (not standard Expo Go).
 */
export async function registerDeviceForPush(
  fcmToken: string,
  platform: 'android' | 'ios' | 'web' = 'android'
): Promise<string | null> {
  if (!geoSenseApi.getToken() || !fcmToken) return null;
  try {
    const res = await geoSenseApi.registerFcmDevice(fcmToken, platform);
    return res.device_id;
  } catch {
    return null;
  }
}

export function resolveAlertDeepLink(alertType?: string, role: 'citizen' | 'officer' = 'citizen'): ScreenName {
  if (role === 'officer') {
    return 'officer-alerts';
  }
  if (alertType === 'HEAVY_RAINFALL') return 'safety-outlook';
  if (alertType === 'VERIFIED_INCIDENT') return 'evacuation';
  return 'alerts';
}
