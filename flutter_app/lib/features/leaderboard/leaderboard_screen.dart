import 'package:material_ui/material_ui.dart';

import '../../core/theme/app_theme.dart';
import '../../core/widgets/app_components.dart';

class LeaderboardScreen extends StatefulWidget {
  const LeaderboardScreen({super.key});
  @override
  State<LeaderboardScreen> createState() => _LeaderboardScreenState();
}

class _LeaderboardScreenState extends State<LeaderboardScreen> {
  int selected = 0;

  @override
  Widget build(BuildContext context) {
    final isIndividuals = selected == 0;
    return ScreenShell(
      title: 'Leaderboard',
      subtitle: 'Rankings will use verified KTP Life data after integration.',
      child: Column(
        children: [
          const MockBadge(),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: SegmentedButton<int>(
              segments: const [
                ButtonSegment(value: 0, label: Text('Individuals')),
                ButtonSegment(value: 1, label: Text('Pledge class')),
              ],
              selected: {selected},
              showSelectedIcon: false,
              onSelectionChanged: (value) =>
                  setState(() => selected = value.first),
            ),
          ),
          const SizedBox(height: 20),
          AppCard(
            padding: const EdgeInsets.fromLTRB(24, 30, 24, 28),
            child: Column(
              children: [
                Container(
                  width: 64,
                  height: 64,
                  decoration: BoxDecoration(
                    color: AppColors.blue.withValues(alpha: .12),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    isIndividuals
                        ? Icons.person_search_outlined
                        : Icons.groups_outlined,
                    color: AppColors.blue,
                    size: 30,
                  ),
                ),
                const SizedBox(height: 16),
                Text(
                  isIndividuals
                      ? 'No individual rankings yet'
                      : 'No pledge class rankings yet',
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  isIndividuals
                      ? 'Member rankings will appear when KTP Life member data and verified points are connected.'
                      : 'Pledge class standings will appear when KTP Life class data and verified points are connected.',
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: AppColors.muted,
                    fontSize: 13,
                    height: 1.45,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          const AppCard(
            padding: EdgeInsets.all(16),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 18,
                  backgroundColor: AppColors.raised,
                  child: Icon(
                    Icons.lock_outline_rounded,
                    color: AppColors.muted,
                    size: 18,
                  ),
                ),
                SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Your ranking',
                        style: TextStyle(fontWeight: FontWeight.w700),
                      ),
                      Text(
                        'Available after account integration',
                        style: TextStyle(color: AppColors.muted, fontSize: 12),
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
}
