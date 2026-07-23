import os

BASE_DIR = r"c:\Users\user\Desktop\Development\SMS\mobile\apps\eduorbit"

def create_file(path, content):
    full_path = os.path.join(BASE_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

pubspec_yaml = """name: eduorbit_app
description: EduOrbit Main Application
version: 1.0.0+1
publish_to: none

environment:
  sdk: ">=3.0.0 <4.0.0"
  flutter: ">=3.0.0"

dependencies:
  flutter:
    sdk: flutter
  flutter_localizations:
    sdk: flutter
  eduorbit_core:
    path: ../../packages/core
  eduorbit_design_system:
    path: ../../packages/design_system
  responsive_framework: ^1.1.0
  flutter_riverpod: ^2.4.3
  go_router: ^12.1.1
  hive: ^2.2.3
"""
create_file("pubspec.yaml", pubspec_yaml)

entry_main = """import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'app.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const ProviderScope(child: EduOrbitApp()));
}
"""
create_file("lib/main_development.dart", entry_main)
create_file("lib/main_staging.dart", entry_main)
create_file("lib/main_production.dart", entry_main)

app_dart = """import 'package:flutter/material.dart';
import 'package:responsive_framework/responsive_framework.dart';
import 'router/app_router.dart';

class EduOrbitApp extends StatelessWidget {
  const EduOrbitApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'EduOrbit',
      theme: ThemeData.light(), // Replace with eduorbit_design_system theme
      routerConfig: appRouter,
      builder: (context, child) => ResponsiveBreakpoints.builder(
        child: child!,
        breakpoints: [
          const Breakpoint(start: 0, end: 450, name: MOBILE),
          const Breakpoint(start: 451, end: 800, name: TABLET),
          const Breakpoint(start: 801, end: 1920, name: DESKTOP),
          const Breakpoint(start: 1921, end: double.infinity, name: '4K'),
        ],
      ),
    );
  }
}
"""
create_file("lib/app.dart", app_dart)

app_router_dart = """import 'package:go_router/go_router.dart';
import 'package:flutter/material.dart';

final appRouter = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const Scaffold(body: Center(child: Text('Splash'))),
    ),
  ],
);
"""
create_file("lib/router/app_router.dart", app_router_dart)
create_file("lib/router/route_names.dart", "class RouteNames {\n  static const String home = 'home';\n}\n")

shells = [
    ("parent_shell.dart", "ParentShell", "Home, Fees, Attendance, Chat, More"),
    ("student_shell.dart", "StudentShell", "Home, Courses, Exams, Library, More"),
    ("teacher_shell.dart", "TeacherShell", "Home, Classes, Attendance, Grades, More"),
    ("staff_shell.dart", "StaffShell", "Home, HR, Workflow, Facilities, More"),
    ("school_admin_shell.dart", "SchoolAdminShell", "Home, Students, Staff, Finance, Settings"),
    ("super_admin_shell.dart", "SuperAdminShell", "Home, Schools, Subscriptions, Health, Settings"),
]
for file_name, class_name, nav in shells:
    content = f"""import 'package:flutter/material.dart';

class {class_name} extends StatelessWidget {{
  final Widget child;
  const {class_name}({{super.key, required this.child}});

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      body: child,
      bottomNavigationBar: BottomNavigationBar(
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
          BottomNavigationBarItem(icon: Icon(Icons.more_horiz), label: 'More'),
        ],
      ),
    );
  }}
}}
"""
    create_file(f"lib/shells/{file_name}", content)

modules = [
    ("auth", ["login_screen", "mfa_screen", "forgot_password_screen", "biometric_setup_screen"]),
    ("dashboard", ["parent_dashboard_screen", "student_dashboard_screen", "teacher_dashboard_screen", "staff_dashboard_screen", "school_admin_dashboard_screen", "super_admin_dashboard_screen"]),
    ("academic", []),
    ("students", []),
    ("attendance", []),
    ("timetable", []),
    ("lms", []),
    ("assessment", []),
    ("exams", []),
    ("finance", []),
    ("communication", []),
    ("hr", []),
    ("library", []),
    ("transport", []),
    ("hostel", []),
    ("clinic", []),
    ("inventory", []),
    ("workflow", []),
    ("facilities", []),
    ("ai_assistant", ["ai_chat_screen", "ai_voice_screen", "ai_knowledge_screen", "chat_bubble", "streaming_text"]), # extra widgets and screens
    ("admin", []),
]

def to_camel_case(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def to_pascal_case(snake_str):
    return ''.join(x.title() for x in snake_str.split('_'))

for mod, extras in modules:
    mod_path = f"lib/features/{mod}"
    pascal_mod = to_pascal_case(mod)
    camel_mod = to_camel_case(mod)
    
    # Models
    create_file(f"{mod_path}/data/models/{mod}_model.dart", f"class {pascal_mod}Model {{}}\n")
    # Remote Source
    create_file(f"{mod_path}/data/datasources/{mod}_remote_source.dart", f"class {pascal_mod}RemoteSource {{}}\n")
    # Local Source
    create_file(f"{mod_path}/data/datasources/{mod}_local_source.dart", f"class {pascal_mod}LocalSource {{}}\n")
    # Repository Impl
    create_file(f"{mod_path}/data/repositories/{mod}_repository_impl.dart", f"import '../../domain/repositories/{mod}_repository.dart';\nclass {pascal_mod}RepositoryImpl implements {pascal_mod}Repository {{}}\n")
    # Entity
    create_file(f"{mod_path}/domain/entities/{mod}_entity.dart", f"class {pascal_mod}Entity {{}}\n")
    # Repository interface
    create_file(f"{mod_path}/domain/repositories/{mod}_repository.dart", f"abstract class {pascal_mod}Repository {{}}\n")
    # Use case
    create_file(f"{mod_path}/domain/usecases/get_{mod}_list.dart", f"class Get{pascal_mod}List {{}}\n")
    # Provider
    create_file(f"{mod_path}/presentation/providers/{mod}_provider.dart", f"import 'package:flutter_riverpod/flutter_riverpod.dart';\nfinal {camel_mod}Provider = Provider((ref) => null);\n")
    
    if mod not in ["auth", "dashboard", "ai_assistant"]:
        create_file(f"{mod_path}/presentation/screens/{mod}_screen.dart", f"import 'package:flutter/material.dart';\nclass {pascal_mod}Screen extends StatelessWidget {{\n  const {pascal_mod}Screen({{super.key}});\n  @override\n  Widget build(BuildContext context) => const Scaffold();\n}}\n")
        create_file(f"{mod_path}/presentation/screens/{mod}_detail_screen.dart", f"import 'package:flutter/material.dart';\nclass {pascal_mod}DetailScreen extends StatelessWidget {{\n  const {pascal_mod}DetailScreen({{super.key}});\n  @override\n  Widget build(BuildContext context) => const Scaffold();\n}}\n")
    
    for extra in extras:
        pascal_extra = to_pascal_case(extra)
        if extra in ["chat_bubble", "streaming_text"]:
            create_file(f"{mod_path}/presentation/widgets/{extra}.dart", f"import 'package:flutter/material.dart';\nclass {pascal_extra} extends StatelessWidget {{\n  const {pascal_extra}({{super.key}});\n  @override\n  Widget build(BuildContext context) => const SizedBox();\n}}\n")
        else:
            create_file(f"{mod_path}/presentation/screens/{extra}.dart", f"import 'package:flutter/material.dart';\nclass {pascal_extra} extends StatelessWidget {{\n  const {pascal_extra}({{super.key}});\n  @override\n  Widget build(BuildContext context) => const Scaffold();\n}}\n")

print("Scaffolding complete.")
