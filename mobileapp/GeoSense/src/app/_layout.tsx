import React, { useEffect } from 'react';
import { Slot } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { AppProvider } from '@/context/AppContext';

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  useEffect(() => {
    // Hide splash screen smoothly on mount
    SplashScreen.hideAsync().catch(() => {});
  }, []);

  return (
    <AppProvider>
      <Slot />
    </AppProvider>
  );
}
