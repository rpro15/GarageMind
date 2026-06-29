enum DrivingStyle { comfort, sport, economy }
enum Season { summer, winter, allSeason }

class TireRequest {
  final String brand;
  final String model;
  final int year;
  final DrivingStyle drivingStyle;
  final Season? season;
  final int? budget;

  TireRequest({
    required this.brand,
    required this.model,
    required this.year,
    required this.drivingStyle,
    this.season,
    this.budget,
  });

  Map<String, dynamic> toJson() => {
    'brand': brand,
    'model': model,
    'year': year,
    'driving_style': drivingStyle.name,
    'season': season?.name.replaceAll('allSeason', 'all_season'),
    'budget': budget,
  };
}
