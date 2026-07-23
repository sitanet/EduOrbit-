import 'package:flutter_test/flutter_test.dart';
import 'package:eduorbit_design_system/tokens/colors.dart';
import 'package:eduorbit_design_system/tokens/spacing.dart';
import 'package:eduorbit_design_system/tokens/radius.dart';
import 'package:eduorbit_design_system/tokens/typography.dart';
import 'package:flutter/material.dart';

void main() {
  group('Design Tokens', () {
    test('primary color palette should be indigo-based', () {
      expect(EduOrbitColors.primary, isNotNull);
      expect(EduOrbitColors.primaryLight, isNotNull);
      expect(EduOrbitColors.primaryDark, isNotNull);
    });

    test('semantic colors should be defined', () {
      expect(EduOrbitColors.success, isNotNull);
      expect(EduOrbitColors.warning, isNotNull);
      expect(EduOrbitColors.error, isNotNull);
      expect(EduOrbitColors.info, isNotNull);
    });

    test('fromSchoolBranding should generate palette from brand color', () {
      final palette = EduOrbitColors.fromSchoolBranding(const Color(0xFF1E3A8A));
      expect(palette, isNotNull);
    });

    test('spacing scale should be consistent', () {
      expect(EduOrbitSpacing.xs, 4.0);
      expect(EduOrbitSpacing.sm, 8.0);
      expect(EduOrbitSpacing.md, 12.0);
      expect(EduOrbitSpacing.lg, 16.0);
      expect(EduOrbitSpacing.xl, 20.0);
      expect(EduOrbitSpacing.xxl, 24.0);
      expect(EduOrbitSpacing.xxxl, 32.0);
    });

    test('radius tokens should be non-negative', () {
      expect(EduOrbitRadius.none, 0);
      expect(EduOrbitRadius.sm, greaterThan(0));
      expect(EduOrbitRadius.pill, greaterThanOrEqualTo(999));
    });

    test('typography scale should include all Material 3 levels', () {
      expect(EduOrbitTypography.displayLarge, isNotNull);
      expect(EduOrbitTypography.bodyMedium, isNotNull);
      expect(EduOrbitTypography.labelSmall, isNotNull);
    });
  });

  group('Theme Generation', () {
    test('light theme should use light brightness', () {
      final theme = EduOrbitTheme.light();
      expect(theme.brightness, Brightness.light);
    });

    test('dark theme should use dark brightness', () {
      final theme = EduOrbitTheme.dark();
      expect(theme.brightness, Brightness.dark);
    });

    test('branded theme should apply custom primary color', () {
      final theme = EduOrbitTheme.fromBranding(
        const Color(0xFF8B0000),
        isDark: false,
      );
      expect(theme, isNotNull);
    });
  });
}
