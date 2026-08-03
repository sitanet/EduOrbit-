import 'package:flutter_test/flutter_test.dart';
import 'package:eduorbit/app.dart';

void main() {
  testWidgets('EduOrbit App initializes properly', (WidgetTester tester) async {
    await tester.pumpWidget(const EduOrbitApp());
    expect(find.byType(EduOrbitApp), findsOneWidget);
  });
}
