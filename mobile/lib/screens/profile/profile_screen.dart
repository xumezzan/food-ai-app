import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';
import '../../models/user.dart';
import '../../services/user_service.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _weightController = TextEditingController();
  final _heightController = TextEditingController();
  String _goal = 'maintain';
  bool _isSaving = false;
  bool _isLoading = true;

  final _goals = const [
    {'value': 'loss', 'label': 'Похудение', 'icon': '📉'},
    {'value': 'gain', 'label': 'Набор массы', 'icon': '💪'},
    {'value': 'maintain', 'label': 'Поддержание', 'icon': '⚖️'},
  ];

  @override
  void initState() {
    super.initState();
    _loadSaved();
  }

  Future<void> _loadSaved() async {
    final user = await UserService.loadProfile();
    if (user != null) {
      _weightController.text = user.weight.toString();
      _heightController.text = user.height.toString();
      setState(() => _goal = user.goal);
    }
    setState(() => _isLoading = false);
  }

  Future<void> _save() async {
    final weight = double.tryParse(_weightController.text);
    final height = double.tryParse(_heightController.text);

    if (weight == null || height == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Введи корректные вес и рост')),
      );
      return;
    }

    setState(() => _isSaving = true);

    try {
      await UserService.saveProfile(
        User(weight: weight, height: height, goal: _goal),
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Профиль сохранён ✅'),
          backgroundColor: AppTheme.primary,
        ),
      );
      Navigator.pop(context);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Ошибка: $e'), backgroundColor: Colors.red),
      );
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  @override
  void dispose() {
    _weightController.dispose();
    _heightController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Мой профиль')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Вес
            _label('Вес (кг)'),
            const SizedBox(height: 8),
            _inputField(controller: _weightController, hint: '70'),
            const SizedBox(height: 20),

            // Рост
            _label('Рост (см)'),
            const SizedBox(height: 8),
            _inputField(controller: _heightController, hint: '175'),
            const SizedBox(height: 28),

            // Цель
            _label('Цель'),
            const SizedBox(height: 12),
            ..._goals.map((g) => _GoalTile(
                  icon: g['icon']!,
                  label: g['label']!,
                  value: g['value']!,
                  selected: _goal == g['value'],
                  onTap: () => setState(() => _goal = g['value']!),
                )),
            const SizedBox(height: 40),

            // Кнопка сохранить
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _isSaving ? null : _save,
                child: _isSaving
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(
                          color: Colors.white,
                          strokeWidth: 2,
                        ),
                      )
                    : const Text('Сохранить'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _label(String text) => Text(
        text,
        style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15),
      );

  Widget _inputField({
    required TextEditingController controller,
    required String hint,
  }) {
    return TextField(
      controller: controller,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      decoration: InputDecoration(
        hintText: hint,
        filled: true,
        fillColor: Colors.white,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: Colors.grey.shade200),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: Colors.grey.shade200),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppTheme.primary, width: 1.5),
        ),
      ),
    );
  }
}

class _GoalTile extends StatelessWidget {
  final String icon;
  final String label;
  final String value;
  final bool selected;
  final VoidCallback onTap;

  const _GoalTile({
    required this.icon,
    required this.label,
    required this.value,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: selected ? AppTheme.primary.withOpacity(0.08) : Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: selected ? AppTheme.primary : Colors.grey.shade200,
            width: selected ? 1.5 : 1,
          ),
        ),
        child: Row(
          children: [
            Text(icon, style: const TextStyle(fontSize: 22)),
            const SizedBox(width: 14),
            Text(
              label,
              style: TextStyle(
                fontSize: 15,
                fontWeight: selected ? FontWeight.w600 : FontWeight.normal,
                color: selected ? AppTheme.primary : const Color(0xFF1A1A2E),
              ),
            ),
            const Spacer(),
            if (selected)
              const Icon(Icons.check_circle, color: AppTheme.primary, size: 20),
          ],
        ),
      ),
    );
  }
}
