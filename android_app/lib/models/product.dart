class Product {
  final String id;
  final String name;
  final double price;
  final String currency;
  final String? imageUrl;
  final String? partnerLink;
  final String? source;
  final double? rating;

  Product({
    required this.id,
    required this.name,
    required this.price,
    this.currency = 'RUB',
    this.imageUrl,
    this.partnerLink,
    this.source,
    this.rating,
  });

  factory Product.fromJson(Map<String, dynamic> json) {
    return Product(
      id: json['id']?.toString() ?? '',
      name: json['name'] as String? ?? '',
      price: (json['price'] as num).toDouble(),
      currency: json['currency'] as String? ?? 'RUB',
      imageUrl: json['image_url'] as String?,
      partnerLink: json['partner_link'] as String?,
      source: json['source'] as String?,
      rating: (json['rating'] as num?)?.toDouble(),
    );
  }
}

class RecommendationResult {
  final String advice;
  final List<Product> products;
  final Product? popularPick;

  RecommendationResult({
    required this.advice,
    required this.products,
    this.popularPick,
  });

  factory RecommendationResult.fromJson(Map<String, dynamic> json) {
    return RecommendationResult(
      advice: json['advice'] as String? ?? '',
      products: (json['products'] as List?)
              ?.map((p) => Product.fromJson(p as Map<String, dynamic>))
              .toList() ??
          [],
      popularPick: json['popular_pick'] != null
          ? Product.fromJson(json['popular_pick'] as Map<String, dynamic>)
          : null,
    );
  }
}
