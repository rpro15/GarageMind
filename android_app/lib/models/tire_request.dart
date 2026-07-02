/// Синхронизировано с Python: app/domain/models.py
enum DrivingStyle { comfort, sport, economy }

enum Season { summer, winter, allSeason }

enum ProductType { tires, wheels, bolts, assembly }

enum DeliverySpeed { any, within3Days, withinWeek, urgent }

enum OrderType { pickup, delivery }

class TirePreferences {
  final int? tireWidth;
  final int? tireProfile;
  final int? tireDiameter;
  final String? wheelMaterial; // "steel" | "alloy"
  final int? wheelDiameter;
  final ProductType productType;
  final DeliverySpeed deliverySpeed;
  final OrderType orderType;
  final List<String> preferredBrands;
  final bool onlyInStock;

  TirePreferences({
    this.tireWidth,
    this.tireProfile,
    this.tireDiameter,
    this.wheelMaterial,
    this.wheelDiameter,
    this.productType = ProductType.tires,
    this.deliverySpeed = DeliverySpeed.any,
    this.orderType = OrderType.delivery,
    this.preferredBrands = const [],
    this.onlyInStock = true,
  });

  Map<String, dynamic> toJson() => {
    'tire_width': tireWidth,
    'tire_profile': tireProfile,
    'tire_diameter': tireDiameter,
    'wheel_material': wheelMaterial,
    'wheel_diameter': wheelDiameter,
    'product_type': productType.name,
    'delivery_speed': deliverySpeed.name,
    'order_type': orderType.name,
    'preferred_brands': preferredBrands,
    'only_in_stock': onlyInStock,
  };
}

class UserLocation {
  final String region;
  final String city;
  final String? deliveryCity;
  final String searchScope; // "region" | "all"

  UserLocation({
    this.region = 'Москва',
    this.city = 'Москва',
    this.deliveryCity,
    this.searchScope = 'region',
  });

  Map<String, dynamic> toJson() => {
    'region': region,
    'city': city,
    'delivery_city': deliveryCity ?? city,
    'search_scope': searchScope,
  };
}

class TireRequest {
  final String brand;
  final String model;
  final int year;
  final DrivingStyle drivingStyle;
  final Season? season;
  final int? budget;
  final TirePreferences preferences;
  final UserLocation location;

  TireRequest({
    required this.brand,
    required this.model,
    required this.year,
    required this.drivingStyle,
    this.season,
    this.budget,
    this.preferences = const TirePreferences(),
    this.location = const UserLocation(),
  });

  Map<String, dynamic> toJson() => {
    'brand': brand,
    'model': model,
    'year': year,
    'driving_style': drivingStyle.name,
    'season': season?.name.replaceAll('allSeason', 'all_season'),
    'budget': budget,
    'preferences': preferences.toJson(),
    'location': location.toJson(),
  };
}
