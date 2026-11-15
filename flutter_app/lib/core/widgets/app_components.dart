import 'package:material_ui/material_ui.dart';

import '../theme/app_theme.dart';

class AppCard extends StatelessWidget {
  const AppCard({required this.child, this.padding, this.onTap, super.key});
  final Widget child;
  final EdgeInsetsGeometry? padding;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final card = Container(
      width: double.infinity,
      padding: padding ?? const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: Colors.white.withValues(alpha: .04)),
      ),
      child: child,
    );
    return onTap == null
        ? card
        : InkWell(
            onTap: onTap,
            borderRadius: BorderRadius.circular(22),
            child: card,
          );
  }
}

class ScreenShell extends StatelessWidget {
  const ScreenShell({
    required this.title,
    required this.child,
    this.subtitle,
    this.actions,
    super.key,
  });
  final String title;
  final String? subtitle;
  final Widget child;
  final List<Widget>? actions;

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(actions: actions),
    body: SafeArea(
      top: false,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
        children: [
          Text(title, style: Theme.of(context).textTheme.headlineLarge),
          if (subtitle != null) ...[const SizedBox(height: 8), Text(subtitle!)],
          const SizedBox(height: 28),
          child,
        ],
      ),
    ),
  );
}

class SectionHeading extends StatelessWidget {
  const SectionHeading(this.text, {this.trailing, super.key});
  final String text;
  final Widget? trailing;
  @override
  Widget build(BuildContext context) => Row(
    children: [
      Expanded(
        child: Text(text, style: Theme.of(context).textTheme.headlineSmall),
      ),
      ?trailing,
    ],
  );
}

class MockBadge extends StatelessWidget {
  const MockBadge({super.key});
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
    decoration: BoxDecoration(
      color: AppColors.blue.withValues(alpha: .14),
      borderRadius: BorderRadius.circular(99),
    ),
    child: const Text(
      'PROTOTYPE DATA',
      style: TextStyle(
        color: AppColors.blue,
        fontSize: 10,
        fontWeight: FontWeight.w800,
        letterSpacing: .6,
      ),
    ),
  );
}
