class Product {
  final int? id;
  final String name;
  final String? barcode;
  final double calories;
  final double protein;
  final double fat;
  final double carbs;
  final String? verdict;
  final String? verdictText;
  final bool verdictIsMock;

  Product({
    this.id,
    required this.name,
    this.barcode,
    required this.calories,
    required this.protein,
    required this.fat,
    required this.carbs,
    this.verdict,
    this.verdictText,
    this.verdictIsMock = false,
  });

  factory Product.fromJson(Map<String, dynamic> json) {
    return Product(
      id: json['id'],
      name: json['name'] ?? '',
      barcode: json['barcode'],
      calories: (json['calories'] as num).toDouble(),
      protein: (json['protein'] as num).toDouble(),
      fat: (json['fat'] as num).toDouble(),
      carbs: (json['carbs'] as num).toDouble(),
      verdict: json['verdict'],
      verdictText: json['verdict_text'],
      verdictIsMock: json['verdict_is_mock'] ?? false,
    );
  }
}

