import { Platform } from 'react-native';

export const Colors = {
  // Brand palette from GeoSense Design Specs
  primary: '#00875A', // Emerald green
  primaryDark: '#0D5C3A', // Field officer header green
  primaryForest: '#064E3B',
  primaryLight: '#E8F5E9',
  primaryMint: '#D1FAE5',
  
  // Risk colors
  riskHigh: '#EF4444', // Red for 87% high risk
  riskCritical: '#DC2626',
  riskModerate: '#F59E0B', // Amber
  riskLow: '#10B981', // Mint green
  
  // UI neutrals
  background: '#F8FAFC',
  cardBackground: '#FFFFFF',
  textPrimary: '#0F172A',
  textSecondary: '#64748B',
  textMuted: '#94A3B8',
  border: '#E2E8F0',
  borderLight: '#F1F5F9',
  
  // Status & Badges
  badgeRedBg: '#FEE2E2',
  badgeRedText: '#DC2626',
  badgeGreenBg: '#D1FAE5',
  badgeGreenText: '#065F46',
  badgeOrangeBg: '#FEF3C7',
  badgeOrangeText: '#B45309',

  light: {
    text: '#0F172A',
    background: '#F8FAFC',
    backgroundElement: '#FFFFFF',
    backgroundSelected: '#E8F5E9',
    textSecondary: '#64748B',
    link: '#00875A',
  },
  dark: {
    text: '#F8FAFC',
    background: '#0F172A',
    backgroundElement: '#1E293B',
    backgroundSelected: '#064E3B',
    textSecondary: '#94A3B8',
    link: '#10B981',
  },
} as const;

export type ThemeColor = keyof typeof Colors.light & keyof typeof Colors.dark;

export const Fonts = Platform.select({
  ios: {
    sans: 'system-ui',
    serif: 'ui-serif',
    rounded: 'ui-rounded',
    mono: 'ui-monospace',
  },
  default: {
    sans: 'normal',
    serif: 'serif',
    rounded: 'normal',
    mono: 'monospace',
  },
});

export const Spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  xxxl: 32,
  half: 2,
  one: 4,
  two: 8,
  three: 12,
  four: 16,
  five: 20,
  six: 24,
  seven: 28,
} as const;

export const MaxContentWidth = 600;
export const BottomTabInset = 70;
