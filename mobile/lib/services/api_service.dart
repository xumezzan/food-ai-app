import 'dart:io';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../core/constants/api_constants.dart';
import '../models/product.dart';
import 'auth_service.dart';

/// Результат сканирования — имя продукта + флаг заглушки
class ScanResult {
  final String detectedName;
  final bool isMock;
  const ScanResult({required this.detectedName, required this.isMock});
}

class ApiService {
  // ─── Декодирование UTF-8 ────────────────────────────────────────────────

  static Map<String, dynamic> _decode(http.Response r) =>
      jsonDecode(utf8.decode(r.bodyBytes));

  static List<dynamic> _decodeList(http.Response r) =>
      jsonDecode(utf8.decode(r.bodyBytes));

  // ─── Auth заголовки ──────────────────────────────────────────────────────

  /// Возвращает заголовки с Firebase ID Token.
  /// Вызывается перед каждым запросом — Firebase обновляет токен автоматически.
  static Future<Map<String, String>> _authHeaders({bool isJson = false}) async {
    final token = await AuthService.getIdToken();
    return {
      if (isJson) 'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  // ─── Scan ────────────────────────────────────────────────────────────────

  /// Отправляет фото → Gemini Vision → возвращает ScanResult
  /// Требует авторизацию. Учитывает лимит 50 сканов/день.
  static Future<ScanResult> scanFood(File imageFile) async {
    final token = await AuthService.getIdToken();
    final request = http.MultipartRequest('POST', Uri.parse(ApiConstants.scan));

    if (token != null) {
      request.headers['Authorization'] = 'Bearer $token';
    }

    request.files.add(
      await http.MultipartFile.fromPath('file', imageFile.path),
    );

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 200) {
      final data = _decode(response);
      return ScanResult(
        detectedName: data['detected_name'] as String,
        isMock: data['is_mock'] as bool? ?? false,
      );
    }

    // 429 — превышен лимит сканирований
    if (response.statusCode == 429) {
      final data = _decode(response);
      final detail = data['detail'] as Map<String, dynamic>?;
      throw RateLimitException(
        message: detail?['message'] ?? 'Лимит сканирований исчерпан',
        count: detail?['count'] as int? ?? 50,
        limit: detail?['limit'] as int? ?? 50,
      );
    }

    if (response.statusCode == 401) {
      throw const UnauthorizedException();
    }

    throw Exception('Ошибка распознавания: ${response.statusCode}');
  }

  // ─── Analyze ─────────────────────────────────────────────────────────────

  static Future<Product> analyzeFood(String name, int userId) async {
    final response = await http.post(
      Uri.parse(ApiConstants.analyze),
      headers: await _authHeaders(isJson: true),
      body: jsonEncode({'name': name, 'user_id': userId}),
    );
    if (response.statusCode == 200) {
      return Product.fromJson(_decode(response));
    }
    throw Exception('Ошибка анализа: ${response.statusCode}');
  }

  // ─── Barcode ─────────────────────────────────────────────────────────────

  static Future<Product> getProductByBarcode(String barcode, {int? userId}) async {
    final uri = Uri.parse(ApiConstants.barcode).replace(
      queryParameters: {
        'code': barcode,
        if (userId != null) 'user_id': userId.toString(),
      },
    );
    final response = await http.get(uri, headers: await _authHeaders());
    if (response.statusCode == 200) {
      return Product.fromJson(_decode(response));
    } else if (response.statusCode == 404) {
      throw Exception('Продукт не найден');
    }
    throw Exception('Ошибка сервера: ${response.statusCode}');
  }

  // ─── Search ──────────────────────────────────────────────────────────────

  static Future<List<Product>> searchProducts(String query) async {
    if (query.length < 2) return [];
    final uri = Uri.parse(ApiConstants.productSearch)
        .replace(queryParameters: {'q': query});
    final response = await http.get(uri, headers: await _authHeaders());
    if (response.statusCode == 200) {
      return _decodeList(response).map((j) => Product.fromJson(j)).toList();
    }
    return [];
  }

  // ─── Correct Product ─────────────────────────────────────────────────────

  static Future<Product> correctProduct({
    required String barcode,
    required int productId,
    int? userId,
  }) async {
    final response = await http.post(
      Uri.parse(ApiConstants.correctProduct),
      headers: await _authHeaders(isJson: true),
      body: jsonEncode({
        'barcode': barcode,
        'product_id': productId,
        if (userId != null) 'user_id': userId,
      }),
    );
    if (response.statusCode == 200) {
      return Product.fromJson(_decode(response));
    }
    throw Exception('Ошибка исправления: ${response.statusCode}');
  }

  // ─── Auth Usage ──────────────────────────────────────────────────────────

  /// Возвращает статус лимита сканирований для отображения в UI.
  static Future<Map<String, dynamic>> getScanUsage() async {
    final response = await http.get(
      Uri.parse('${ApiConstants.baseUrl}/auth/usage'),
      headers: await _authHeaders(),
    );
    if (response.statusCode == 200) {
      return _decode(response);
    }
    return {'count': 0, 'limit': 50, 'remaining': 50};
  }
}

// ─────────────────────────────────────────────
// Кастомные исключения
// ─────────────────────────────────────────────

class RateLimitException implements Exception {
  final String message;
  final int count;
  final int limit;

  const RateLimitException({
    required this.message,
    required this.count,
    required this.limit,
  });

  @override
  String toString() => message;
}

class UnauthorizedException implements Exception {
  const UnauthorizedException();

  @override
  String toString() => 'Необходима авторизация. Войдите в приложение.';
}
