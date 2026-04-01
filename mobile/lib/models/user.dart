class User {
  final double weight;
  final double height;
  final String goal; // loss | gain | maintain

  User({
    required this.weight,
    required this.height,
    required this.goal,
  });

  Map<String, dynamic> toJson() => {
        'weight': weight,
        'height': height,
        'goal': goal,
      };

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      weight: (json['weight'] as num).toDouble(),
      height: (json['height'] as num).toDouble(),
      goal: json['goal'],
    );
  }
}
