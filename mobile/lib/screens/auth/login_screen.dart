import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';
import '../../services/auth_service.dart';

/// Экран входа — отображается если пользователь не авторизован.
///
/// Минималистичный дизайн: логотип + два кнопки (Google, Apple).
/// После успешного входа app.dart автоматически перенаправит на HomeScreen
/// через Stream<User?> authStateChanges.
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  bool _loading = false;

  Future<void> _handleSignIn(Future<void> Function() signInFn) async {
    setState(() => _loading = true);
    try {
      await signInFn();
      // Успех — authStateChanges в app.dart перекинет на HomeScreen автоматически
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('$e'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Spacer(flex: 2),

              // ─── Логотип ───────────────────────────────────────────────
              Container(
                width: 88,
                height: 88,
                decoration: BoxDecoration(
                  color: AppTheme.primary,
                  borderRadius: BorderRadius.circular(24),
                  boxShadow: [
                    BoxShadow(
                      color: AppTheme.primary.withOpacity(0.35),
                      blurRadius: 20,
                      offset: const Offset(0, 8),
                    ),
                  ],
                ),
                child: const Icon(Icons.restaurant_menu, color: Colors.white, size: 44),
              ),
              const SizedBox(height: 24),

              const Text(
                'Food AI',
                style: TextStyle(fontSize: 32, fontWeight: FontWeight.w800, letterSpacing: -1),
              ),
              const SizedBox(height: 8),
              const Text(
                'Сканируй. Анализируй. Питайся правильно.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 15, color: Color(0xFF6C757D), height: 1.4),
              ),

              const Spacer(flex: 2),

              // ─── Кнопки входа ──────────────────────────────────────────
              if (_loading)
                const CircularProgressIndicator()
              else ...[
                // Google Sign-In
                _SignInButton(
                  label: 'Войти через Google',
                  icon: _GoogleIcon(),
                  backgroundColor: Colors.white,
                  textColor: const Color(0xFF1A1A2E),
                  onPressed: () => _handleSignIn(
                    () async => await AuthService.signInWithGoogle(),
                  ),
                ),
                const SizedBox(height: 12),

                // Apple Sign-In
                _SignInButton(
                  label: 'Войти через Apple',
                  icon: const Icon(Icons.apple, color: Colors.white, size: 22),
                  backgroundColor: Colors.black,
                  textColor: Colors.white,
                  onPressed: () => _handleSignIn(
                    () async => await AuthService.signInWithApple(),
                  ),
                ),
              ],

              const SizedBox(height: 12),
              const Text(
                'Войдя, вы соглашаетесь с Условиями использования',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 12, color: Color(0xFFADB5BD)),
              ),

              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────
// Кнопка входа
// ─────────────────────────────────────────────

class _SignInButton extends StatelessWidget {
  final String label;
  final Widget icon;
  final Color backgroundColor;
  final Color textColor;
  final VoidCallback onPressed;

  const _SignInButton({
    required this.label,
    required this.icon,
    required this.backgroundColor,
    required this.textColor,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 54,
      child: ElevatedButton(
        onPressed: onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: backgroundColor,
          foregroundColor: textColor,
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: BorderSide(color: Colors.grey.shade200),
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            icon,
            const SizedBox(width: 12),
            Text(label, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────
// Google иконка (цветная G)
// ─────────────────────────────────────────────

class _GoogleIcon extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return const Text(
      'G',
      style: TextStyle(
        fontSize: 20,
        fontWeight: FontWeight.w800,
        color: Color(0xFF4285F4), // Google Blue
      ),
    );
  }
}
