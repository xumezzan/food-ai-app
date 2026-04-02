import 'dart:io';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../core/constants/api_constants.dart';
import '../models/product.dart';

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

  // Базовые JSON-заголовки (без авторизации — MVP mode)
  static const Map<String, String> _jsonHeaders = {
    'Content-Type': 'application/json',
  };

  // ─── Scan ────────────────────────────────────────────────────────────────

  /// Отправляет фото → Gemini Vision → возвращает ScanResult.
  /// Лимит: 50 сканирований в день с одного IP.
  static Future<ScanResult> scanFood(File imageFile) async {
    final request = http.MultipartRequest('POST', Uri.parse(ApiConstants.scan));
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
      throw const RateLimitException();
    }

    throw Exception('Ошибка распознавания: ${response.statusCode}');
  }

  // ─── Analyze ─────────────────────────────────────────────────────────────

  static Future<Product> analyzeFood(String name, int userId) async {
    final response = await http.post(
      Uri.parse(ApiConstants.analyze),
      headers: _jsonHeaders,
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
    final response = await http.get(uri);
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
    final response = await http.get(uri);
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
      headers: _jsonHeaders,
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
}

// ─────────────────────────────────────────────
// Кастомные исключения
// ─────────────────────────────────────────────

class RateLimitException implements Exception {
  const RateLimitException();

  @override
  String toString() =>
      'Лимит 50 сканирований в день исчерпан. Попробуйте завтра.';
}
