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
  // Декодируем байты явно — защита от кривой кириллицы
  static Map<String, dynamic> _decode(http.Response r) =>
      jsonDecode(utf8.decode(r.bodyBytes));

  static List<dynamic> _decodeList(http.Response r) =>
      jsonDecode(utf8.decode(r.bodyBytes));

  /// Отправляет фото → Gemini Vision → возвращает ScanResult
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
    throw Exception('Ошибка распознавания');
  }

  /// Анализирует продукт по имени с учётом цели пользователя
  static Future<Product> analyzeFood(String name, int userId) async {
    final response = await http.post(
      Uri.parse(ApiConstants.analyze),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'name': name, 'user_id': userId}),
    );
    if (response.statusCode == 200) {
      return Product.fromJson(_decode(response));
    }
    throw Exception('Ошибка анализа');
  }

  /// Поиск по штрихкоду + AI-вердикт (если передан userId)
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
    throw Exception('Ошибка сервера');
  }

  /// Поиск продуктов по строке — для dropdown автодополнения
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

  /// Отправляет исправление → возвращает обновлённый продукт с новым вердиктом
  static Future<Product> correctProduct({
    required String barcode,
    required int productId,
    int? userId,
  }) async {
    final response = await http.post(
      Uri.parse(ApiConstants.correctProduct),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'barcode': barcode,
        'product_id': productId,
        if (userId != null) 'user_id': userId,
      }),
    );
    if (response.statusCode == 200) {
      return Product.fromJson(_decode(response));
    }
    throw Exception('Ошибка исправления');
  }
}
