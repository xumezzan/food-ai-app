import 'package:flutter/material.dart';
import '../core/theme/app_theme.dart';

class ScanButton extends StatelessWidget {
  final VoidCallback onPressed;
  final bool isLoading;

  const ScanButton({
    super.key,
    required this.onPressed,
    this.isLoading = false,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: isLoading ? null : onPressed,
      child: Container(
        width: 160,
        height: 160,
        decoration: BoxDecoration(
          color: isLoading ? AppTheme.textSecondary : AppTheme.primary,
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(
              color: AppTheme.primary.withOpacity(0.35),
              blurRadius: 24,
              offset: const Offset(0, 8),
            ),
          ],
        ),
        child: isLoading
            ? const Center(
                child: CircularProgressIndicator(color: Colors.white),
              )
            : const Icon(
                Icons.camera_alt_outlined,
                color: Colors.white,
                size: 56,
              ),
      ),
    );
  }
}
