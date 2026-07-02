/// Синхронизировано с Python: app/domain/models.py
class Product {
  final String id;
  final String name;
  final double price;
  final String currency;
  final String? imageUrl;
  final String? partnerLink;
  final String? source;
  final double? rating;
  
  // Новые поля
  final String productType; // "tires" | "wheels" | "bolts" | "assembly"
  final bool inStock;
  final int? deliveryDays;
  final double? deliveryPrice;
  final bool pickupAvailable;
  final int? warrantyMonths;
  
  // Размер шин
  final int? tireWidth;
  final int? tireProfile;
  final int? tireDiameter;
  
  // Диски
  final String? wheelMaterial;
  final int? wheelDiameter;
  
  // Крепёж
  final String? boltThread;  // "M12x1.5"
  final String? boltHead;    // "17mm", "секретка"

  Product({
    required this.id,
    required this.name,
    required this.price,
    this.currency = 'RUB',
    this.imageUrl,
    this.partnerLink,
    this.source,
    this.rating,
    this.productType = 'tires',
    this.inStock = true,
    this.deliveryDays,
    this.deliveryPrice,
    this.pickupAvailable = false,
    this.warrantyMonths,
    this.tireWidth,
    this.tireProfile,
    this.tireDiameter,
    this.wheelMaterial,
    this.wheelDiameter,
    this.boltThread,
    this.boltHead,
  });

  /// Форматированный размер шин: "205/55 R16"
  String? get tireSize {
    if (tireWidth != null && tireProfile != null && tireDiameter != null) {
      return '${tireWidth}/${tireProfile} R$tireDiameter';
    }
    return null;
  }

  /// Иконка для типа товара
  String get typeIcon {
    switch (productType) {
      case 'wheels': return '🛞';
      case 'bolts': return '🔩';
      case 'assembly': return '⚙️';
      default: return '🛞';
    }
  }

  /// Цвет для бейджа типа
  int get typeColor {
    switch (productType) {
      case 'wheels': return 0xFF00D4FF;
      case 'bolts': return 0xFFFFD700;
      case 'assembly': return 0xFF00FF88;
      default: return 0xFF556677;
    }
  }

  factory Product.fromJson(Map<String, dynamic> json) {
    return Product(
      id: json['id']?.toString() ?? '',
      name: json['name'] as String? ?? '',
      price: (json['price'] as num?)?.toDouble() ?? 0.0,
      currency: json['currency'] as String? ?? 'RUB',
      imageUrl: json['image_url'] as String?,
      partnerLink: json['partner_link'] as String?,
      source: json['source'] as String?,
      rating: (json['rating'] as num?)?.toDouble(),
      productType: json['product_type'] as String? ?? 'tires',
      inStock: json['in_stock'] as bool? ?? true,
      deliveryDays: json['delivery_days'] as int?,
      deliveryPrice: (json['delivery_price'] as num?)?.toDouble(),
      pickupAvailable: json['pickup_available'] as bool? ?? false,
      warrantyMonths: json['warranty_months'] as int?,
      tireWidth: json['tire_width'] as int?,
      tireProfile: json['tire_profile'] as int?,
      tireDiameter: json['tire_diameter'] as int?,
      wheelMaterial: json['wheel_material'] as String?,
      wheelDiameter: json['wheel_diameter'] as int?,
      boltThread: json['bolt_thread'] as String?,
      boltHead: json['bolt_head'] as String?,
    );
  }
}

class RecommendationResult {
  final String advice;
  final List<Product> products;
  final Product? popularPick;
  final List<String> warnings;
  
  // Дополнительные подборки
  final List<Product> compatibleWheels;
  final List<Product> compatibleBolts;

  RecommendationResult({
    required this.advice,
    required this.products,
    this.popularPick,
    this.warnings = const [],
    this.compatibleWheels = const [],
    this.compatibleBolts = const [],
  });

  factory RecommendationResult.fromJson(Map<String, dynamic> json) {
    return RecommendationResult(
      advice: json['advice'] as String? ?? '',
      products: _parseProducts(json['products']),
      popularPick: json['popular_pick'] != null
          ? Product.fromJson(json['popular_pick'] as Map<String, dynamic>)
          : null,
      warnings: (json['warnings'] as List?)?.cast<String>() ?? [],
      compatibleWheels: _parseProducts(json['compatible_wheels']),
      compatibleBolts: _parseProducts(json['compatible_bolts']),
    );
  }

  static List<Product> _parseProducts(dynamic data) {
    if (data is List) {
      return data
          .map((p) => Product.fromJson(p as Map<String, dynamic>))
          .toList();
    }
    return [];
  }
}
