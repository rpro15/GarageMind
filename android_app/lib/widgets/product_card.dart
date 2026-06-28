import 'package:flutter/material.dart';
import '../main.dart';

class ProductCard extends StatelessWidget {
  final ProductItem product;
  const ProductCard({super.key, required this.product});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF131B2C),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF1B2740)),
      ),
      child: Row(
        children: [
          // Изображение-заглушка
          Container(
            width: 56, height: 56,
            decoration: BoxDecoration(
              color: const Color(0xFF080B14),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: const Color(0xFF1B2740)),
            ),
            child: const Icon(
              Icons.circle_outlined,
              color: Color(0xFF00D4FF),
              size: 28,
            ),
          ),
          const SizedBox(width: 12),

          // Информация
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  product.name,
                  style: const TextStyle(
                    color: Color(0xFFE8EDF5),
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 4),
                Text(
                  '${product.price.toStringAsFixed(0)} ₽',
                  style: const TextStyle(
                    color: Color(0xFF00D4FF),
                    fontWeight: FontWeight.w700,
                    fontSize: 15,
                  ),
                ),
                Text(
                  product.source.toUpperCase(),
                  style: const TextStyle(
                    color: Color(0xFF2E4060),
                    fontSize: 10,
                    letterSpacing: 0.5,
                  ),
                ),
              ],
            ),
          ),

          // Кнопка
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 8),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF00D4FF), Color(0xFF0088CC)],
              ),
              borderRadius: BorderRadius.circular(30),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF00D4FF).withOpacity(0.2),
                  blurRadius: 12,
                ),
              ],
            ),
            child: const Text(
              'Купить',
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.w600,
                fontSize: 12,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
