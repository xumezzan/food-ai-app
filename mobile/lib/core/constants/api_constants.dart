class ApiConstants {
  // Для локальной разработки — Android эмулятор использует 10.0.2.2,
  // iOS симулятор и реальный девайс — localhost / IP машины
  static const String baseUrl = 'http://192.168.0.53:8000';

  static const String scan = '$baseUrl/scan';
  static const String analyze = '$baseUrl/analyze';
  static const String product = '$baseUrl/product';
  static const String productSearch = '$baseUrl/product/search';
  static const String correction = '$baseUrl/correction';
  static const String user = '$baseUrl/user';
  static const String barcode = '$baseUrl/barcode';
  static const String correctProduct = '$baseUrl/correct-product';
}
