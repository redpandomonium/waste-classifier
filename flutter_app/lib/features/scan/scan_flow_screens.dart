import 'package:material_ui/material_ui.dart';

import '../../core/theme/app_theme.dart';
import '../../core/widgets/app_components.dart';

void _open(BuildContext context, Widget screen) =>
    Navigator.push(context, MaterialPageRoute<void>(builder: (_) => screen));

class ScanIntroductionScreen extends StatelessWidget {
  const ScanIntroductionScreen({super.key});
  @override
  Widget build(BuildContext context) => ScreenShell(
    title: 'Scan Waste',
    subtitle: 'Learn where an item belongs before you dispose of it.',
    child: Column(
      children: [
        const _HeroIcon(icon: Icons.recycling_rounded),
        const SizedBox(height: 22),
        const AppCard(
          child: Column(
            children: [
              _Step(
                number: '1',
                text: 'Choose or take a clear photo of one waste item.',
              ),
              SizedBox(height: 20),
              _Step(
                number: '2',
                text: 'Review a mock classification and disposal guidance.',
              ),
              SizedBox(height: 20),
              _Step(
                number: '3',
                text: 'Submit a second mock photo to preview verification.',
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        const Text(
          'Prototype only — no camera, model, uploads, verification, or points are active.',
          textAlign: TextAlign.center,
          style: TextStyle(color: AppColors.muted, fontSize: 13),
        ),
        const SizedBox(height: 22),
        FilledButton(
          onPressed: () => _open(context, const PhotoSelectionScreen()),
          child: const Text('Get started'),
        ),
      ],
    ),
  );
}

class PhotoSelectionScreen extends StatelessWidget {
  const PhotoSelectionScreen({super.key});
  @override
  Widget build(BuildContext context) => ScreenShell(
    title: 'Add a photo',
    subtitle: 'Center one item and keep the background clear.',
    child: Column(
      children: [
        Container(
          height: 250,
          width: double.infinity,
          decoration: BoxDecoration(
            color: AppColors.card,
            borderRadius: BorderRadius.circular(26),
            border: Border.all(color: Colors.white12),
          ),
          child: const Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.image_outlined, color: AppColors.muted, size: 64),
              SizedBox(height: 12),
              Text(
                'Photo preview',
                style: TextStyle(fontWeight: FontWeight.w700, fontSize: 17),
              ),
              SizedBox(height: 4),
              Text(
                'No image is captured in this prototype',
                style: TextStyle(color: AppColors.muted, fontSize: 13),
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),
        FilledButton.icon(
          onPressed: () => _open(context, const ClassificationResultScreen()),
          icon: const Icon(Icons.camera_alt_rounded),
          label: const Text('Simulate taking photo'),
        ),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          onPressed: () => _open(context, const ClassificationResultScreen()),
          style: OutlinedButton.styleFrom(
            minimumSize: const Size.fromHeight(54),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
            ),
          ),
          icon: const Icon(Icons.photo_library_outlined),
          label: const Text('Simulate choosing photo'),
        ),
      ],
    ),
  );
}

class ClassificationResultScreen extends StatelessWidget {
  const ClassificationResultScreen({super.key});
  @override
  Widget build(BuildContext context) => ScreenShell(
    title: 'Review result',
    subtitle: 'This is a sample result, not a machine-learning prediction.',
    child: Column(
      children: [
        const MockBadge(),
        const SizedBox(height: 16),
        const AppCard(
          child: Column(
            children: [
              CircleAvatar(
                radius: 38,
                backgroundColor: Color(0x224285F4),
                child: Icon(
                  Icons.local_drink_outlined,
                  color: AppColors.blue,
                  size: 38,
                ),
              ),
              SizedBox(height: 16),
              Text(
                'Sample: Plastic bottle',
                style: TextStyle(fontSize: 23, fontWeight: FontWeight.w800),
              ),
              SizedBox(height: 6),
              Text(
                'Mock category: Recyclable',
                style: TextStyle(
                  color: AppColors.success,
                  fontWeight: FontWeight.w700,
                ),
              ),
              SizedBox(height: 18),
              Divider(color: Color(0xFF343434)),
              SizedBox(height: 12),
              Text(
                'Empty and rinse the bottle. Check local rules before placing it in a recycling bin.',
                textAlign: TextAlign.center,
                style: TextStyle(color: AppColors.muted, height: 1.5),
              ),
            ],
          ),
        ),
        const SizedBox(height: 24),
        FilledButton(
          onPressed: () => _open(context, const DisposalInstructionsScreen()),
          child: const Text('Continue to disposal steps'),
        ),
      ],
    ),
  );
}

class DisposalInstructionsScreen extends StatelessWidget {
  const DisposalInstructionsScreen({super.key});
  @override
  Widget build(BuildContext context) => ScreenShell(
    title: 'Dispose responsibly',
    subtitle: 'Follow the sample guidance, then preview verification.',
    child: Column(
      children: [
        const AppCard(
          child: Column(
            children: [
              _Instruction(
                icon: Icons.water_drop_outlined,
                title: 'Empty and rinse',
                detail: 'Remove remaining liquid or residue.',
              ),
              Divider(height: 28, color: Color(0xFF343434)),
              _Instruction(
                icon: Icons.compress_rounded,
                title: 'Keep it loose',
                detail: 'Do not bag recyclable items.',
              ),
              Divider(height: 28, color: Color(0xFF343434)),
              _Instruction(
                icon: Icons.delete_outline_rounded,
                title: 'Use the right bin',
                detail: 'Confirm the local recycling label first.',
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        const Text(
          'Guidance is illustrative and may differ by municipality.',
          textAlign: TextAlign.center,
          style: TextStyle(color: AppColors.muted, fontSize: 13),
        ),
        const SizedBox(height: 24),
        FilledButton(
          onPressed: () => _open(context, const SecondPhotoScreen()),
          child: const Text('I’m ready to verify'),
        ),
      ],
    ),
  );
}

class SecondPhotoScreen extends StatelessWidget {
  const SecondPhotoScreen({super.key});
  @override
  Widget build(BuildContext context) => ScreenShell(
    title: 'Show the disposal',
    subtitle: 'A future phase will verify disposal with a second photo.',
    child: Column(
      children: [
        const _HeroIcon(icon: Icons.add_a_photo_outlined),
        const SizedBox(height: 24),
        const AppCard(
          child: Text(
            'Continue with a simulated submission. No photo is taken, stored, or uploaded.',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.muted, height: 1.5),
          ),
        ),
        const SizedBox(height: 24),
        FilledButton.icon(
          onPressed: () => _open(context, const VerificationResultScreen()),
          icon: const Icon(Icons.camera_alt_rounded),
          label: const Text('Simulate second photo'),
        ),
      ],
    ),
  );
}

class VerificationResultScreen extends StatelessWidget {
  const VerificationResultScreen({super.key});
  @override
  Widget build(BuildContext context) => ScreenShell(
    title: 'Prototype complete',
    subtitle: 'This demonstrates the intended experience only.',
    child: Column(
      children: [
        const _HeroIcon(
          icon: Icons.check_circle_outline_rounded,
          color: AppColors.success,
        ),
        const SizedBox(height: 24),
        const AppCard(
          child: Column(
            children: [
              MockBadge(),
              SizedBox(height: 16),
              Text(
                'Sample verification result',
                style: TextStyle(fontSize: 21, fontWeight: FontWeight.w800),
              ),
              SizedBox(height: 8),
              Text(
                'No disposal was verified and no points were awarded.',
                textAlign: TextAlign.center,
                style: TextStyle(color: AppColors.muted, height: 1.5),
              ),
              SizedBox(height: 18),
              Text(
                '+0 points',
                style: TextStyle(
                  color: AppColors.blue,
                  fontSize: 26,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 24),
        FilledButton(
          onPressed: () =>
              Navigator.popUntil(context, (route) => route.isFirst),
          child: const Text('Return to dashboard'),
        ),
      ],
    ),
  );
}

class _HeroIcon extends StatelessWidget {
  const _HeroIcon({required this.icon, this.color = AppColors.blue});
  final IconData icon;
  final Color color;
  @override
  Widget build(BuildContext context) => Container(
    width: 112,
    height: 112,
    decoration: BoxDecoration(
      color: color.withValues(alpha: .12),
      shape: BoxShape.circle,
    ),
    child: Icon(icon, color: color, size: 54),
  );
}

class _Step extends StatelessWidget {
  const _Step({required this.number, required this.text});
  final String number;
  final String text;
  @override
  Widget build(BuildContext context) => Row(
    children: [
      CircleAvatar(
        radius: 16,
        backgroundColor: AppColors.blue,
        child: Text(
          number,
          style: const TextStyle(fontWeight: FontWeight.w800),
        ),
      ),
      const SizedBox(width: 14),
      Expanded(
        child: Text(
          text,
          style: const TextStyle(color: AppColors.muted, height: 1.4),
        ),
      ),
    ],
  );
}

class _Instruction extends StatelessWidget {
  const _Instruction({
    required this.icon,
    required this.title,
    required this.detail,
  });
  final IconData icon;
  final String title;
  final String detail;
  @override
  Widget build(BuildContext context) => Row(
    children: [
      Container(
        width: 44,
        height: 44,
        decoration: BoxDecoration(
          color: AppColors.blue.withValues(alpha: .12),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Icon(icon, color: AppColors.blue),
      ),
      const SizedBox(width: 14),
      Expanded(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: const TextStyle(fontWeight: FontWeight.w700)),
            const SizedBox(height: 3),
            Text(
              detail,
              style: const TextStyle(color: AppColors.muted, fontSize: 13),
            ),
          ],
        ),
      ),
    ],
  );
}
