import 'package:flutter_test/flutter_test.dart';
import 'package:kt_sustainability/app.dart';
import 'package:kt_sustainability/core/theme/app_theme.dart';
import 'package:kt_sustainability/features/leaderboard/leaderboard_screen.dart';
import 'package:kt_sustainability/features/scan/scan_flow_screens.dart';
import 'package:material_ui/material_ui.dart';

void setViewport(WidgetTester tester, Size size) {
  tester.view.devicePixelRatio = 1;
  tester.view.physicalSize = size;
}

void main() {
  final mobileSizes = <Size>[
    const Size(375, 667),
    const Size(393, 852),
    const Size(400, 770),
    const Size(430, 932),
  ];

  testWidgets('dashboard is responsive at reviewed mobile sizes', (
    tester,
  ) async {
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    for (final size in mobileSizes) {
      setViewport(tester, size);
      await tester.pumpWidget(const KtSustainabilityApp());
      await tester.pump();

      expect(find.text('Sustainability'), findsOneWidget);
      expect(find.text('Your Points'), findsOneWidget);
      expect(find.text('Verified Scans'), findsOneWidget);
      expect(find.text('Start Scanning'), findsOneWidget);
      expect(tester.takeException(), isNull, reason: 'Failed at $size');
    }
  });

  testWidgets('dashboard uses honest integration placeholders', (tester) async {
    setViewport(tester, const Size(400, 770));
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(const KtSustainabilityApp());

    expect(find.text('Not yet tracked'), findsNWidgets(2));
    expect(find.text('Available after KTP Life integration'), findsNWidgets(2));
    expect(find.text('PLACEHOLDER'), findsOneWidget);
    expect(find.text('Jordan M.'), findsNothing);
    expect(find.text('Alpha Beta'), findsNothing);
  });

  testWidgets('primary scan action opens the guided flow', (tester) async {
    setViewport(tester, const Size(375, 667));
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(const KtSustainabilityApp());

    await tester.tap(find.byKey(const Key('start-scanning-button')));
    await tester.pumpAndSettle();
    expect(find.text('Get started'), findsOneWidget);

    await tester.drag(find.byType(ListView), const Offset(0, -300));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Get started'));
    await tester.pumpAndSettle();
    expect(find.text('Add a photo'), findsOneWidget);
    expect(find.text('Simulate taking photo'), findsOneWidget);

    await tester.tap(find.byTooltip('Back'));
    await tester.pumpAndSettle();
    expect(find.text('Get started'), findsOneWidget);
  });

  testWidgets('scan and verification screens fit the smallest viewport', (
    tester,
  ) async {
    setViewport(tester, const Size(375, 667));
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    const screens = <Widget>[
      ScanIntroductionScreen(),
      PhotoSelectionScreen(),
      ClassificationResultScreen(),
      DisposalInstructionsScreen(),
      SecondPhotoScreen(),
      VerificationResultScreen(),
      LeaderboardScreen(),
    ];

    for (final screen in screens) {
      await tester.pumpWidget(MaterialApp(theme: AppTheme.dark, home: screen));
      await tester.pump();
      expect(
        tester.takeException(),
        isNull,
        reason: '${screen.runtimeType} overflowed',
      );
    }
  });

  testWidgets('leaderboard shows empty states for both categories', (
    tester,
  ) async {
    setViewport(tester, const Size(393, 852));
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      MaterialApp(theme: AppTheme.dark, home: const LeaderboardScreen()),
    );

    expect(find.text('No individual rankings yet'), findsOneWidget);
    await tester.tap(find.text('Pledge class'));
    await tester.pump();
    expect(find.text('No pledge class rankings yet'), findsOneWidget);
    expect(find.text('0 pts'), findsNothing);
  });
}
