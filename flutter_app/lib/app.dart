import 'package:material_ui/material_ui.dart';

import 'core/theme/app_theme.dart';
import 'features/dashboard/dashboard_screen.dart';

class KtSustainabilityApp extends StatelessWidget {
  const KtSustainabilityApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'KTSustainability',
    debugShowCheckedModeBanner: false,
    theme: AppTheme.dark,
    home: const SustainabilityDashboardScreen(),
  );
}
