import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { Path } from 'react-native-svg';

interface GeoSenseLogoProps {
  color?: string;
  textColor?: string;
  size?: number;
  showText?: boolean;
  textSize?: number;
}

export function GeoSenseLogo({
  color = '#00A86B',
  textColor = '#0F172A',
  size = 28,
  showText = true,
  textSize = 22,
}: GeoSenseLogoProps) {
  return (
    <View style={styles.container}>
      <Svg width={size} height={size * 0.85} viewBox="0 0 34 28" fill="none">
        {/* Left peak outline / polygon */}
        <Path
          d="M3 24L13 5L20 18"
          stroke={color}
          strokeWidth="3.2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {/* Right peak / facet */}
        <Path
          d="M17 14L23 3L31 24H3"
          stroke={color}
          strokeWidth="3.2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </Svg>
      {showText && (
        <Text style={[styles.text, { color: textColor, fontSize: textSize }]}>
          Geo<Text style={{ fontWeight: '700' }}>Sense</Text>
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  text: {
    fontWeight: '600',
    letterSpacing: -0.5,
  },
});

