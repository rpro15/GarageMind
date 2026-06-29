class CarBrand {
  final String name;
  final List<String> models;

  CarBrand({required this.name, required this.models});

  factory CarBrand.fromJson(Map<String, dynamic> json) {
    return CarBrand(
      name: json['name'] as String,
      models: List<String>.from(json['models'] as List),
    );
  }
}
