import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../core/constants/api_constants.dart';
import '../models/user.dart';

class UserService {
  static const _keyUserId = 'user_id';
  static const _keyWeight = 'user_weight';
  static const _keyHeight = 'user_height';
  static const _keyGoal = 'user_goal';

  /// Сохраняет профиль локально + отправляет на backend.
  /// Возвращает user_id.
  static Future<int> saveProfile(User user) async {
    // 1. Отправляем на backend
    final response = await http.post(
      Uri.parse(ApiConstants.user),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(user.toJson()),
    );

    if (response.statusCode != 201) {
      throw Exception('Ошибка сохранения профиля: ${response.statusCode}');
    }

    final userId = jsonDecode(response.body)['id'] as int;

    // 2. Сохраняем локально
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(_keyUserId, userId);
    await prefs.setDouble(_keyWeight, user.weight);
    await prefs.setDouble(_keyHeight, user.height);
    await prefs.setString(_keyGoal, user.goal);

    return userId;
  }

  /// Загружает профиль из локального хранилища.
  /// Возвращает null, если профиль ещё не создан.
  static Future<User?> loadProfile() async {
    final prefs = await SharedPreferences.getInstance();
    final weight = prefs.getDouble(_keyWeight);
    final height = prefs.getDouble(_keyHeight);
    final goal = prefs.getString(_keyGoal);

    if (weight == null || height == null || goal == null) return null;

    return User(weight: weight, height: height, goal: goal);
  }

  /// Возвращает сохранённый user_id или null.
  static Future<int?> getUserId() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getInt(_keyUserId);
  }
}
