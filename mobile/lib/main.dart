import 'package:flutter/material.dart';
import 'app.dart';
import 'core/localization/language_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await LanguageService.init();
  runApp(const App());
}
