import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/product.dart';

class ProductCard extends StatelessWidget {
  final Product product;
  final bool isBestPrice;
  final bool isPopular;

  const ProductCard({
    super.key,
    required this.product,
    this.isBestPrice = false,
    this.isPopular = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      child: Stack(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: const Color(0xFF111820),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: isBestPrice
                    ? const Color(0xFFFFD700).withOpacity(0.3)
                    : const Color(0xFF1A2630),
              ),
            ),
            child: Row(
              children: [
                // Изображение
                Container(
                  width: 56,
                  height: 56,
                  decoration: BoxDecoration(
                    color: const Color(0xFF0A0D14),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFF1A2630)),
                  ),
                  child: product.imageUrl != null
                      ? ClipRRect(
                          borderRadius: BorderRadius.circular(12),
                          child: Image.network(
                            product.imageUrl!,
                            fit: BoxFit.cover,
                            errorBuilder: (_, __, ___) => const Icon(
                              Icons.image_outlined,
                              color: Color(0xFF556677),
                            ),
                          ),
                        )
                      : const Icon(Icons.image_outlined, color: Color(0xFF556677)),
                ),
                const SizedBox(width: 12),
                // Инфо
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        product.name,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 13,
                          fontWeight: FontWeight.w500,
                        ),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          if (product.rating != null) ...[
                            const Icon(Icons.star, color: Color(0xFFFFD700), size: 12),
                            const SizedBox(width: 2),
                            Text(
                              product.rating!.toStringAsFixed(1),
                              style: const TextStyle(color: Color(0xFF8899AA), fontSize: 11),
                            ),
                            const SizedBox(width: 8),
                          ],
                          Text(
                            '${product.price.toStringAsFixed(0)} ₽',
                            style: TextStyle(
                              color: isBestPrice
                                  ? const Color(0xFFFFD700)
                                  : const Color(0xFF00D4FF),
                              fontSize: 14,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                      if (product.source != null)
                        Text(
                          product.source!,
                          style: const TextStyle(color: Color(0xFF556677), fontSize: 11),
                        ),
                    ],
                  ),
                ),
                // Кнопка
                Container(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: isBestPrice
                          ? [const Color(0xFFFFD700), const Color(0xFFE6C200)]
                          : [const Color(0xFF00D4FF), const Color(0xFF0088CC)],
                    ),
                    borderRadius: BorderRadius.circular(30),
                  ),
                  child: TextButton(
                    onPressed: () => _openLink(product.partnerLink),
                    child: Text(
                      isBestPrice ? 'Выбрать' : 'Купить',
                      style: const TextStyle(
                        color: Colors.black,
                        fontWeight: FontWeight.bold,
                        fontSize: 12,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          // Бейдж лучшей цены
          if (isBestPrice)
            Positioned(
              top: -4,
              left: 8,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFFFFD700), Color(0xFFE6C200)],
                  ),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.crown, size: 10, color: Colors.black),
                    SizedBox(width: 3),
                    Text(
                      'Лучшая цена',
                      style: TextStyle(
                        color: Colors.black,
                        fontSize: 9,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }

  void _openLink(String? url) {
    if (url != null) {
      launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
    }
  }
}
