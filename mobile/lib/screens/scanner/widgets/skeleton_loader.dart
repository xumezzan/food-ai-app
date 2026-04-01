import 'package:flutter/material.dart';

/// Анимированный skeleton — мигающая серая плашка
class SkeletonBox extends StatefulWidget {
  final double width;
  final double height;
  final double borderRadius;

  const SkeletonBox({
    super.key,
    required this.width,
    required this.height,
    this.borderRadius = 8,
  });

  @override
  State<SkeletonBox> createState() => _SkeletonBoxState();
}

class _SkeletonBoxState extends State<SkeletonBox>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    )..repeat(reverse: true);

    _animation = Tween(begin: 0.4, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _animation,
      builder: (_, __) => Opacity(
        opacity: _animation.value,
        child: Container(
          width: widget.width,
          height: widget.height,
          decoration: BoxDecoration(
            color: const Color(0xFFE0E0E0),
            borderRadius: BorderRadius.circular(widget.borderRadius),
          ),
        ),
      ),
    );
  }
}

/// Skeleton-макет Bottom Sheet пока идёт загрузка
class ProductSkeleton extends StatelessWidget {
  const ProductSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Название
          const SkeletonBox(width: 200, height: 24),
          const SizedBox(height: 12),
          // Вердикт-бейдж
          const SkeletonBox(width: 100, height: 32, borderRadius: 16),
          const SizedBox(height: 28),
          // Большие калории
          const SkeletonBox(width: 120, height: 56),
          const SizedBox(height: 4),
          const SkeletonBox(width: 60, height: 16),
          const SizedBox(height: 28),
          // БЖУ строка
          Row(
            children: const [
              SkeletonBox(width: 70, height: 60),
              SizedBox(width: 12),
              SkeletonBox(width: 70, height: 60),
              SizedBox(width: 12),
              SkeletonBox(width: 70, height: 60),
            ],
          ),
          const SizedBox(height: 24),
          // Объяснение вердикта
          const SkeletonBox(width: double.infinity, height: 16),
          const SizedBox(height: 8),
          const SkeletonBox(width: 220, height: 16),
        ],
      ),
    );
  }
}
