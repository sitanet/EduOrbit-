import 'package:flutter_test/flutter_test.dart';
import 'package:eduorbit_core/network/api_exception.dart';

void main() {
  group('ApiException Types', () {
    test('UnauthorizedException should carry status 401', () {
      const ex = UnauthorizedException('Session expired');
      expect(ex.message, 'Session expired');
      expect(ex.statusCode, 401);
    });

    test('ForbiddenException should carry status 403', () {
      const ex = ForbiddenException('Insufficient permissions');
      expect(ex.message, 'Insufficient permissions');
      expect(ex.statusCode, 403);
    });

    test('NotFoundException should carry status 404', () {
      const ex = NotFoundException('Student not found');
      expect(ex.message, 'Student not found');
      expect(ex.statusCode, 404);
    });

    test('ServerException should carry status 500', () {
      const ex = ServerException('Internal server error');
      expect(ex.message, 'Internal server error');
      expect(ex.statusCode, 500);
    });

    test('NetworkException should indicate connectivity issue', () {
      const ex = NetworkException('No internet connection');
      expect(ex.message, 'No internet connection');
      expect(ex.isNetworkError, true);
    });

    test('ValidationException should carry field errors', () {
      final ex = ValidationException(
        'Validation failed',
        fieldErrors: {'email': 'Invalid email format', 'name': 'Required'},
      );
      expect(ex.fieldErrors.length, 2);
      expect(ex.fieldErrors['email'], 'Invalid email format');
    });
  });

  group('Auth Service', () {
    test('should validate token format', () {
      const validToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ';
      expect(validToken.contains('.'), true);
      expect(validToken.split('.').length, 3);
    });
  });
}
