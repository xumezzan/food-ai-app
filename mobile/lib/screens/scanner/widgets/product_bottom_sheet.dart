import 'package:flutter/material.dart';
import '../../../models/product.dart';
import '../../../core/theme/app_theme.dart';
import '../../../services/api_service.dart';
import '../../../services/user_service.dart';
import 'skeleton_loader.dart';

class ProductBottomSheet extends StatefulWidget {
  final Product? product;
  final bool isLoading;
  final String? error;
  final String? barcode; // нужен для отправки исправления

  const ProductBottomSheet({
    super.key,
    this.product,
    this.isLoading = false,
    this.error,
    this.barcode,
  });

  @override
  State<ProductBottomSheet> createState() => _ProductBottomSheetState();
}

class _ProductBottomSheetState extends State<ProductBottomSheet> {
  Product? _currentProduct;
  bool _editMode = false;
  bool _correcting = false;

  @override
  void initState() {
    super.initState();
    _currentProduct = widget.product;
  }

  @override
  void didUpdateWidget(ProductBottomSheet oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.product != oldWidget.product) {
      _currentProduct = widget.product;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const SizedBox(height: 12),
          Container(
            width: 40, height: 4,
            decoration: BoxDecoration(
              color: const Color(0xFFE0E0E0),
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 8),
          if (widget.isLoading)
            const ProductSkeleton()
          else if (_currentProduct != null)
            _ProductView(
              product: _currentProduct!,
              editMode: _editMode,
              correcting: _correcting,
              onEditToggle: () => setState(() => _editMode = !_editMode),
              onProductSelected: _onProductSelected,
            )
          else if (widget.error != null)
            _ErrorView(
              message: widget.error!,
              editMode: _editMode,
              correcting: _correcting,
              onEditToggle: () => setState(() => _editMode = !_editMode),
              onProductSelected: _onProductSelected,
            ),
        ],
      ),
    );
  }

  Future<void> _onProductSelected(Product selected) async {
    setState(() {
      _editMode = false;
      _correcting = true;
    });

    try {
      final userId = await UserService.getUserId();
      final updated = await ApiService.correctProduct(
        barcode: widget.barcode ?? '',
        productId: selected.id ?? 0,
        userId: userId,
      );
      if (mounted) setState(() => _currentProduct = updated);
    } catch (_) {
      // при ошибке просто показываем выбранный продукт без вердикта
      if (mounted) setState(() => _currentProduct = selected);
    } finally {
      if (mounted) setState(() => _correcting = false);
    }
  }
}


// ─────────────────────────────────────────────
// Вид продукта
// ─────────────────────────────────────────────

class _ProductView extends StatelessWidget {
  final Product product;
  final bool editMode;
  final bool correcting;
  final VoidCallback onEditToggle;
  final ValueChanged<Product> onProductSelected;

  const _ProductView({
    required this.product,
    required this.editMode,
    required this.correcting,
    required this.onEditToggle,
    required this.onProductSelected,
  });

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

    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 8, 24, 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Название + карандаш + бейдж
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: editMode
                    ? _ProductSearchField(onSelected: onProductSelected)
                    : Text(
                        product.name,
                        style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
              ),
              // Карандаш
              IconButton(
                icon: Icon(
                  editMode ? Icons.close : Icons.edit_outlined,
                  size: 20,
                  color: const Color(0xFF6C757D),
                ),
                onPressed: onEditToggle,
                tooltip: editMode ? 'Отмена' : 'Исправить',
              ),
              // Вердикт только если не редактируем
              if (!editMode && product.verdict != null)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: color.withOpacity(0.4)),
                  ),
                  child: Text(
                    _verdictLabel,
                    style: TextStyle(color: color, fontWeight: FontWeight.w600, fontSize: 11),
                  ),
                ),
            ],
          ),

          // Загрузка исправления
          if (correcting) ...[
            const SizedBox(height: 16),
            const Center(child: CircularProgressIndicator()),
            const SizedBox(height: 16),
          ] else ...[
            const SizedBox(height: 20),

            // Калории
            Text(
              product.calories.toStringAsFixed(0),
              style: const TextStyle(
                fontSize: 56, fontWeight: FontWeight.w800, height: 1,
              ),
            ),
            const Text('ккал на 100 г',
                style: TextStyle(fontSize: 14, color: Color(0xFF6C757D))),
            const SizedBox(height: 20),

            // БЖУ
            Row(
              children: [
                _MacroChip(label: 'Белки', value: product.protein),
                const SizedBox(width: 10),
                _MacroChip(label: 'Жиры', value: product.fat),
                const SizedBox(width: 10),
                _MacroChip(label: 'Углеводы', value: product.carbs),
              ],
            ),

            // Объяснение вердикта
            if (product.verdictText != null) ...[
              const SizedBox(height: 16),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.07),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Text(product.verdictText!,
                    style: const TextStyle(fontSize: 14, height: 1.5)),
              ),
            ],
          ],
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────
// Поле поиска с dropdown
// ─────────────────────────────────────────────

class _ProductSearchField extends StatefulWidget {
  final ValueChanged<Product> onSelected;
  const _ProductSearchField({required this.onSelected});

  @override
  State<_ProductSearchField> createState() => _ProductSearchFieldState();
}

class _ProductSearchFieldState extends State<_ProductSearchField> {
  final _controller = TextEditingController();
  List<Product> _suggestions = [];
  bool _searching = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _onChanged(String q) async {
    if (q.length < 2) {
      setState(() => _suggestions = []);
      return;
    }
    setState(() => _searching = true);
    final results = await ApiService.searchProducts(q);
    if (mounted) setState(() { _suggestions = results; _searching = false; });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TextField(
          controller: _controller,
          autofocus: true,
          decoration: InputDecoration(
            hintText: 'Введи название...',
            filled: true,
            fillColor: const Color(0xFFF8F9FA),
            suffixIcon: _searching
                ? const Padding(
                    padding: EdgeInsets.all(12),
                    child: SizedBox(
                      width: 16, height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                  )
                : null,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide.none,
            ),
            contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          ),
          onChanged: _onChanged,
        ),
        if (_suggestions.isNotEmpty) ...[
          const SizedBox(height: 4),
          Container(
            constraints: const BoxConstraints(maxHeight: 200),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.08),
                  blurRadius: 12,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: ListView.separated(
              shrinkWrap: true,
              itemCount: _suggestions.length,
              separatorBuilder: (_, __) =>
                  const Divider(height: 1, indent: 16),
              itemBuilder: (_, i) {
                final p = _suggestions[i];
                return ListTile(
                  dense: true,
                  title: Text(p.name, style: const TextStyle(fontSize: 14)),
                  trailing: Text(
                    '${p.calories.toStringAsFixed(0)} ккал',
                    style: const TextStyle(
                        fontSize: 12, color: Color(0xFF6C757D)),
                  ),
                  onTap: () => widget.onSelected(p),
                );
              },
            ),
          ),
        ],
      ],
    );
  }
}

// ─────────────────────────────────────────────
// Карточка нутриента
// ─────────────────────────────────────────────

class _MacroChip extends StatelessWidget {
  final String label;
  final double value;
  const _MacroChip({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14),
        decoration: BoxDecoration(
          color: const Color(0xFFF8F9FA),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Column(
          children: [
            Text(
              '${value.toStringAsFixed(1)}г',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 2),
            Text(label,
                style: const TextStyle(fontSize: 12, color: Color(0xFF6C757D))),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────
// Вид ошибки
// ─────────────────────────────────────────────

class _ErrorView extends StatelessWidget {
  final String message;
  final bool editMode;
  final bool correcting;
  final VoidCallback onEditToggle;
  final ValueChanged<Product> onProductSelected;

  const _ErrorView({
    required this.message,
    required this.editMode,
    required this.correcting,
    required this.onEditToggle,
    required this.onProductSelected,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 8, 24, 32),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: editMode
                    ? _ProductSearchField(onSelected: onProductSelected)
                    : const Text(
                        'Продукт не найден',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
              ),
              IconButton(
                icon: Icon(
                  editMode ? Icons.close : Icons.edit_outlined,
                  size: 20,
                  color: const Color(0xFF6C757D),
                ),
                onPressed: onEditToggle,
                tooltip: editMode ? 'Отмена' : 'Добавить вручную',
              ),
            ],
          ),
          if (correcting) ...[
            const SizedBox(height: 16),
            const Center(child: CircularProgressIndicator()),
            const SizedBox(height: 16),
          ] else if (!editMode) ...[
            const SizedBox(height: 32),
            const Icon(Icons.search_off, size: 48, color: Color(0xFF6C757D)),
            const SizedBox(height: 12),
            Text(
              message,
              textAlign: TextAlign.center,
              style: const TextStyle(color: Color(0xFF6C757D), fontSize: 15),
            ),
          ],
        ],
      ),
    );
  }
}

