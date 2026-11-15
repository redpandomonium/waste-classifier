import 'package:material_ui/material_ui.dart';

import '../../core/theme/app_theme.dart';
import '../../core/widgets/app_components.dart';
import '../leaderboard/leaderboard_screen.dart';
import '../scan/scan_flow_screens.dart';

class SustainabilityDashboardScreen extends StatelessWidget {
  const SustainabilityDashboardScreen({super.key});

  void _openScan(BuildContext context) => Navigator.push(
    context,
    MaterialPageRoute<void>(builder: (_) => const ScanIntroductionScreen()),
  );

  void _openLeaderboard(BuildContext context) => Navigator.push(
    context,
    MaterialPageRoute<void>(builder: (_) => const LeaderboardScreen()),
  );

  @override
  Widget build(BuildContext context) => ScreenShell(
    title: 'Sustainability',
    subtitle: 'Make every disposal decision count.',
    actions: const [
      Padding(padding: EdgeInsets.only(right: 20), child: MockBadge()),
    ],
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Row(
          children: [
            Expanded(
              child: _MetricCard(
                icon: Icons.stars_rounded,
                label: 'Your Points',
              ),
            ),
            SizedBox(width: 10),
            Expanded(
              child: _MetricCard(
                icon: Icons.verified_rounded,
                label: 'Verified Scans',
              ),
            ),
          ],
        ),
        const SizedBox(height: 14),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Row(
                children: [
                  _ScanIcon(),
                  SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Scan Waste',
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        SizedBox(height: 3),
                        Text(
                          'Preview the guided disposal flow',
                          style: TextStyle(
                            color: AppColors.muted,
                            fontSize: 14,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 18),
              FilledButton.icon(
                key: const Key('start-scanning-button'),
                onPressed: () => _openScan(context),
                icon: const Icon(Icons.center_focus_strong_rounded),
                label: const Text('Start Scanning'),
              ),
            ],
          ),
        ),
        const SizedBox(height: 28),
        SectionHeading(
          'Leaderboard',
          trailing: TextButton(
            onPressed: () => _openLeaderboard(context),
            child: const Text('View all'),
          ),
        ),
        const SizedBox(height: 12),
        AppCard(
          onTap: () => _openLeaderboard(context),
          child: const Column(
            children: [
              _LeaderboardPlaceholder(
                icon: Icons.person_outline_rounded,
                title: 'Individual rankings',
              ),
              Divider(height: 28, color: Color(0xFF343434)),
              _LeaderboardPlaceholder(
                icon: Icons.groups_outlined,
                title: 'Pledge class rankings',
              ),
            ],
          ),
        ),
        const SizedBox(height: 28),
        const SectionHeading('Your impact'),
        const SizedBox(height: 12),
        const AppCard(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _ImpactPlaceholder(),
              SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _InlinePlaceholderLabel(),
                    SizedBox(height: 9),
                    Text(
                      'Impact tracking coming soon',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    SizedBox(height: 5),
                    Text(
                      'Verified disposal statistics will appear after verification is integrated.',
                      style: TextStyle(
                        color: AppColors.muted,
                        fontSize: 13,
                        height: 1.4,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ],
    ),
  );
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({required this.icon, required this.label});
  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) => AppCard(
    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Row(
          children: [
            Icon(icon, color: AppColors.blue, size: 20),
            const Spacer(),
            const Text(
              '0',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Text(
          label,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(color: AppColors.muted, fontSize: 12),
        ),
        const SizedBox(height: 2),
        const Text(
          'Not yet tracked',
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: TextStyle(color: AppColors.muted, fontSize: 10),
        ),
      ],
    ),
  );
}

class _ScanIcon extends StatelessWidget {
  const _ScanIcon();
  @override
  Widget build(BuildContext context) => Container(
    width: 48,
    height: 48,
    decoration: BoxDecoration(
      color: AppColors.blue.withValues(alpha: .14),
      borderRadius: BorderRadius.circular(15),
    ),
    child: const Icon(Icons.camera_alt_outlined, color: AppColors.blue),
  );
}

class _LeaderboardPlaceholder extends StatelessWidget {
  const _LeaderboardPlaceholder({required this.icon, required this.title});
  final IconData icon;
  final String title;

  @override
  Widget build(BuildContext context) => Row(
    children: [
      CircleAvatar(
        radius: 19,
        backgroundColor: AppColors.raised,
        child: Icon(icon, color: AppColors.blue, size: 20),
      ),
      const SizedBox(width: 12),
      Expanded(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: const TextStyle(fontWeight: FontWeight.w700)),
            const SizedBox(height: 2),
            const Text(
              'Available after KTP Life integration',
              style: TextStyle(color: AppColors.muted, fontSize: 12),
            ),
          ],
        ),
      ),
      const Icon(Icons.chevron_right_rounded, color: AppColors.muted),
    ],
  );
}

class _ImpactPlaceholder extends StatelessWidget {
  const _ImpactPlaceholder();
  @override
  Widget build(BuildContext context) => Container(
    width: 64,
    height: 64,
    alignment: Alignment.center,
    decoration: BoxDecoration(
      shape: BoxShape.circle,
      border: Border.all(color: AppColors.blue, width: 5),
    ),
    child: const Text(
      '—',
      style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
    ),
  );
}

class _InlinePlaceholderLabel extends StatelessWidget {
  const _InlinePlaceholderLabel();
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
    decoration: BoxDecoration(
      color: AppColors.raised,
      borderRadius: BorderRadius.circular(99),
    ),
    child: const Text(
      'PLACEHOLDER',
      style: TextStyle(
        color: AppColors.muted,
        fontSize: 9,
        fontWeight: FontWeight.w800,
        letterSpacing: .5,
      ),
    ),
  );
}
