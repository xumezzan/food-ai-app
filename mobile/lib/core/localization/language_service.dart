import 'package:shared_preferences/shared_preferences.dart';
import 'app_strings.dart';

class LanguageService {
  static const String _langKey = 'selected_language';
  static String currentLanguage = 'ru'; // По умолчанию русский
  
  /// Вызывать один раз в main.dart перед runApp (с await)
  static Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    currentLanguage = prefs.getString(_langKey) ?? 'ru';
  }

  /// Смена языка с сохранением
  static Future<void> changeLanguage(String langCode) async {
    if (langCode == 'ru' || langCode == 'uz') {
      currentLanguage = langCode;
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_langKey, langCode);
    }
  }

  /// Получение перевода по ключу
  static String t(String key) {
    if (!appStrings.containsKey(key)) {
      return key; // Если перевода нет, возвращаем сам ключ
    }
    return appStrings[key]?[currentLanguage] ?? key;
  }
}
