import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Сервис авторизации через Google и Apple (через Firebase Auth).
///
/// Схема работы:
///   1. [signInWithGoogle] / [signInWithApple] — открывает нативный экран логина
///   2. Firebase выдаёт ID Token (JWT, живёт 1 час)
///   3. [getIdToken] — отдаём токен в ApiService для добавления в заголовки
///   4. FastAPI проверяет токен через Firebase Admin SDK
class AuthService {
  static final _auth = FirebaseAuth.instance;
  static const _keyUserId = 'db_user_id';

  // ─── Текущий пользователь ───────────────────────────────────────────────

  /// Возвращает текущего Firebase-пользователя или null.
  static User? get currentUser => _auth.currentUser;

  /// Поток изменений состояния авторизации.
  /// Подержи на него подписку в app.dart для роутинга.
  static Stream<User?> get authStateChanges => _auth.authStateChanges();

  // ─── Google Sign-In ─────────────────────────────────────────────────────

  static Future<UserCredential?> signInWithGoogle() async {
    try {
      // Открываем нативный Google-аккаунт-пикер
      final googleUser = await GoogleSignIn().signIn();
      if (googleUser == null) return null; // Пользователь отменил

      final googleAuth = await googleUser.authentication;
      final credential = GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );

      return await _auth.signInWithCredential(credential);
    } catch (e) {
      throw Exception('Ошибка входа через Google: $e');
    }
  }

  // ─── Apple Sign-In ──────────────────────────────────────────────────────

  static Future<UserCredential?> signInWithApple() async {
    try {
      // Запрашиваем Apple credential
      final appleCredential = await SignInWithApple.getAppleIDCredential(
        scopes: [
          AppleIDAuthorizationScopes.email,
          AppleIDAuthorizationScopes.fullName,
        ],
      );

      // Конвертируем в Firebase credential
      final oauthCredential = OAuthProvider("apple.com").credential(
        idToken: appleCredential.identityToken,
        accessToken: appleCredential.authorizationCode,
      );

      return await _auth.signInWithCredential(oauthCredential);
    } catch (e) {
      throw Exception('Ошибка входа через Apple: $e');
    }
  }

  // ─── Выход ──────────────────────────────────────────────────────────────

  static Future<void> signOut() async {
    await GoogleSignIn().signOut();
    await _auth.signOut();
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_keyUserId);
  }

  // ─── Токен для API запросов ─────────────────────────────────────────────

  /// Возвращает актуальный Firebase ID Token.
  /// Firebase автоматически обновляет токен при истечении (каждый час).
  static Future<String?> getIdToken() async {
    try {
      return await currentUser?.getIdToken();
    } catch (e) {
      return null;
    }
  }

  // ─── Хранение DB user_id ────────────────────────────────────────────────

  static Future<void> saveDbUserId(int userId) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(_keyUserId, userId);
  }

  static Future<int?> getDbUserId() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getInt(_keyUserId);
  }
}
