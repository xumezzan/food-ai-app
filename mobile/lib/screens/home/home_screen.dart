import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../../widgets/scan_button.dart';
import '../../services/api_service.dart';
import '../../services/user_service.dart';
import '../../models/product.dart';
import '../result/result_screen.dart';
import '../profile/profile_screen.dart';
import '../scanner/scanner_screen.dart';


class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _isLoading = false;
  String _statusText = '';
  final _picker = ImagePicker();

  Future<void> _onScan() async {
    // Проверяем, что профиль заполнен
    final userId = await UserService.getUserId();
    if (userId == null) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Сначала заполни профиль 👤'),
          backgroundColor: Colors.orange,
        ),
      );
      Navigator.push(
        context,
        MaterialPageRoute(builder: (_) => const ProfileScreen()),
      );
      return;
    }

    // Шаг 1: открываем камеру
    final XFile? photo = await _picker.pickImage(
      source: ImageSource.camera,
      imageQuality: 85,
    );

    if (photo == null) return;

    setState(() {
      _isLoading = true;
      _statusText = 'Распознаём еду...';
    });

    try {
      // Шаг 2: отправляем фото → Gemini Vision
      final scanResult = await ApiService.scanFood(File(photo.path));

      // Предупреждение если AI работает без ключа
      if (scanResult.isMock && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('⚠️ AI-ключ не настроен — результат приблизительный'),
            backgroundColor: Colors.orange,
            duration: Duration(seconds: 3),
          ),
        );
      }

      setState(() => _statusText = 'Анализируем...');

      // Шаг 3: анализируем продукт с учётом цели
      final Product product = await ApiService.analyzeFood(scanResult.detectedName, userId);


      if (!mounted) return;

      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => ResultScreen(product: product),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Ошибка: $e'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      if (mounted) setState(() {
        _isLoading = false;
        _statusText = '';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Food AI'),
        actions: [
          IconButton(
            icon: const Icon(Icons.person_outline),
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const ProfileScreen()),
            ),
          ),
        ],
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text(
              'Сфотографируй еду',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            const Text(
              'и получи анализ за секунду',
              style: TextStyle(fontSize: 15, color: Color(0xFF6C757D)),
            ),
            const SizedBox(height: 48),
            ScanButton(onPressed: _onScan, isLoading: _isLoading),
            const SizedBox(height: 20),

            // Кнопка сканирования штрихкода
            TextButton.icon(
              onPressed: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const ScannerScreen()),
              ),
              icon: const Icon(Icons.qr_code_scanner),
              label: const Text('Сканировать штрихкод'),
            ),

            const SizedBox(height: 24),
            // Статус загрузки
            AnimatedOpacity(
              opacity: _isLoading ? 1.0 : 0.0,
              duration: const Duration(milliseconds: 300),
              child: Text(
                _statusText,
                style: const TextStyle(
                  fontSize: 14,
                  color: Color(0xFF6C757D),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
