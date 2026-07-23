import 'package:flutter_test/flutter_test.dart';
import 'package:eduorbit_core/config/environment.dart';

void main() {
  group('Environment Configuration', () {
    test('should parse development flavor correctly', () {
      const env = Environment(
        apiUrl: 'http://10.0.2.2:8000',
        appName: 'EduOrbit Dev',
        flavor: Flavor.development,
        enableCrashlytics: false,
        enableAnalytics: false,
        sentryDsn: '',
        logLevel: LogLevel.debug,
      );

      expect(env.apiUrl, 'http://10.0.2.2:8000');
      expect(env.flavor, Flavor.development);
      expect(env.enableCrashlytics, false);
      expect(env.isDevelopment, true);
    });

    test('should parse production flavor correctly', () {
      const env = Environment(
        apiUrl: 'https://api.eduorbit.com',
        appName: 'EduOrbit',
        flavor: Flavor.production,
        enableCrashlytics: true,
        enableAnalytics: true,
        sentryDsn: 'https://prod@sentry.io/eduorbit',
        logLevel: LogLevel.warning,
      );

      expect(env.flavor, Flavor.production);
      expect(env.enableCrashlytics, true);
      expect(env.isProduction, true);
    });
  });

  group('API Endpoints', () {
    test('all 27 module endpoints should be defined', () {
      // Identity & Auth
      expect(ApiEndpoints.login, isNotEmpty);
      expect(ApiEndpoints.refreshToken, isNotEmpty);

      // Academic
      expect(ApiEndpoints.academicYears, isNotEmpty);
      expect(ApiEndpoints.academicClasses, isNotEmpty);

      // Students
      expect(ApiEndpoints.studentProfiles, isNotEmpty);

      // Attendance
      expect(ApiEndpoints.attendanceSessions, isNotEmpty);

      // Finance
      expect(ApiEndpoints.invoices, isNotEmpty);
      expect(ApiEndpoints.payments, isNotEmpty);

      // Communication
      expect(ApiEndpoints.announcements, isNotEmpty);

      // HR
      expect(ApiEndpoints.employees, isNotEmpty);

      // Library
      expect(ApiEndpoints.libraryCatalog, isNotEmpty);

      // Transport
      expect(ApiEndpoints.transportRoutes, isNotEmpty);

      // Hostel
      expect(ApiEndpoints.hostelBuildings, isNotEmpty);

      // Clinic
      expect(ApiEndpoints.clinicPatients, isNotEmpty);

      // Inventory
      expect(ApiEndpoints.inventoryItems, isNotEmpty);

      // Workflow
      expect(ApiEndpoints.workflowDefinitions, isNotEmpty);

      // Facilities
      expect(ApiEndpoints.facilityBuildings, isNotEmpty);

      // Analytics
      expect(ApiEndpoints.dashboards, isNotEmpty);

      // Portal
      expect(ApiEndpoints.portalProfile, isNotEmpty);

      // Administration
      expect(ApiEndpoints.adminSettings, isNotEmpty);

      // AI
      expect(ApiEndpoints.aiChat, isNotEmpty);
    });
  });
}
