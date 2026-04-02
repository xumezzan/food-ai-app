import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import '../../models/product.dart';
import '../../services/api_service.dart';
import '../../services/user_service.dart';
import '../../core/localization/language_service.dart';
import 'widgets/product_bottom_sheet.dart';

class ScannerScreen extends StatefulWidget {
  const ScannerScreen({super.key});

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  final MobileScannerController _cameraController = MobileScannerController();

  // Состояние
  bool _sheetVisible = false;
  bool _isLoading = false;
  Product? _product;
  String? _error;
  String? _lastScanned; // предотвращаем дублирование запросов

  @override
  void dispose() {
    _cameraController.dispose();
    super.dispose();
  }

  Future<void> _onBarcodeDetected(BarcodeCapture capture) async {
    final barcode = capture.barcodes.firstOrNull?.rawValue;
    if (barcode == null || barcode == _lastScanned) return;

    _lastScanned = barcode;
    _cameraController.stop(); // пауза камеры пока показываем результат

    setState(() {
      _sheetVisible = true;
      _isLoading = true;
      _product = null;
      _error = null;
    });

    try {
      final userId = await UserService.getUserId();
      final product = await ApiService.getProductByBarcode(
        barcode,
        userId: userId,
      );
      if (mounted) setState(() => _product = product);
    } catch (e) {
      if (mounted) setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _closeSheet() {
    setState(() {
      _sheetVisible = false;
      _product = null;
      _error = null;
      _lastScanned = null;
    });
    _cameraController.start(); // возобновляем сканирование
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // ── Камера на весь экран ──
          MobileScanner(
            controller: _cameraController,
            onDetect: _onBarcodeDetected,
          ),

          // ── Рамка-прицел ──
          Center(
            child: Container(
              width: 260,
              height: 120,
              decoration: BoxDecoration(
                border: Border.all(color: Colors.white, width: 2.5),
                borderRadius: BorderRadius.circular(16),
              ),
            ),
          ),

          // ── Подсказка сверху ──
          Positioned(
            top: 60,
            left: 0,
            right: 0,
            child: Text(
              LanguageService.t('point_barcode'),
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.w500,
                shadows: [Shadow(color: Colors.black54, blurRadius: 8)],
              ),
            ),
          ),

          // ── Кнопка закрыть ──
          Positioned(
            top: 52,
            right: 16,
            child: IconButton(
              icon: const Icon(Icons.close, color: Colors.white, size: 28),
              onPressed: () => Navigator.pop(context),
            ),
          ),

          // ── Bottom Sheet с анимацией ──
          AnimatedPositioned(
            duration: const Duration(milliseconds: 350),
            curve: Curves.easeOutCubic,
            bottom: _sheetVisible ? 0 : -500,
            left: 0,
            right: 0,
            child: GestureDetector(
              onVerticalDragEnd: (details) {
                if (details.primaryVelocity! > 200) _closeSheet();
              },
              child: ProductBottomSheet(
                product: _product,
                isLoading: _isLoading,
                error: _error,
                barcode: _lastScanned,
              ),
            ),
          ),

          // ── Затемнение фона при открытой шторке ──
          if (_sheetVisible)
            Positioned.fill(
              child: GestureDetector(
                onTap: _closeSheet,
                child: Container(
                  color: Colors.black54,
                  alignment: Alignment.topCenter,
                  child: const SizedBox.expand(),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
