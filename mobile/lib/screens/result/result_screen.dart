import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';
import '../../models/product.dart';

class ResultScreen extends StatelessWidget {
  final Product product;

  const ResultScreen({super.key, required this.product});

  Color get _verdictColor {
    switch (product.verdict) {
      case 'green': return AppTheme.good;
      case 'red':   return AppTheme.bad;
      default:      return AppTheme.ok;
    }
  }

  String get _verdictLabel {
    switch (product.verdict) {
      case 'green': return '🟢 Идеально';
      case 'red':   return '🔴 Не рекомендуется';
      default:      return '🟡 С осторожностью';
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = _verdictColor;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Результат', style: TextStyle(color: Colors.black)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: Padding(
        padding: const EdgeInsets.fromLTRB(24, 16, 24, 32),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Название + вердикт-бейдж
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    product.name,
                    style: const TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF1A1A2E),
                    ),
                  ),
                ),
                if (product.verdict != null) ...[
                  const SizedBox(width: 12),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: color.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: color.withOpacity(0.4)),
                    ),
                    child: Text(
                      _verdictLabel,
                      style: TextStyle(
                        color: color,
                        fontWeight: FontWeight.w600,
                        fontSize: 12,
                      ),
                    ),
                  ),
                ],
              ],
            ),
            const SizedBox(height: 32),

            // Большие калории (как в шторке)
            Text(
              product.calories.toStringAsFixed(0),
              style: const TextStyle(
                fontSize: 64,
                fontWeight: FontWeight.w800,
                height: 1,
                color: Color(0xFF1A1A2E),
              ),
            ),
            const Text(
              'ккал на 100 г',
              style: TextStyle(fontSize: 16, color: Color(0xFF6C757D)),
            ),
            const SizedBox(height: 32),

            // БЖУ строка
            Row(
              children: [
                _MacroChip(label: 'Белки', value: product.protein),
                const SizedBox(width: 12),
                _MacroChip(label: 'Жиры', value: product.fat),
                const SizedBox(width: 12),
                _MacroChip(label: 'Углеводы', value: product.carbs),
              ],
            ),

            // Объяснение вердикта
            if (product.verdictText != null) ...[
              const SizedBox(height: 24),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.07),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Text(
                  product.verdictText!,
                  style: const TextStyle(fontSize: 15, height: 1.5),
                ),
              ),
            ],

            const Spacer(),

            // Кнопка назад
            SizedBox(
              width: double.infinity,
              height: 54,
              child: ElevatedButton(
                onPressed: () => Navigator.pop(context),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.black,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
                child: const Text('Сканировать ещё', style: TextStyle(fontSize: 16)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _MacroChip extends StatelessWidget {
  final String label;
  final double value;
  const _MacroChip({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(
          color: const Color(0xFFF8F9FA),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          children: [
            Text(
              '${value.toStringAsFixed(1)}г',
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: const TextStyle(fontSize: 13, color: Color(0xFF6C757D)),
            ),
          ],
        ),
      ),
    );
  }
}
