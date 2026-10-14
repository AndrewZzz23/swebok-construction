// Ejemplo práctico – "Mis tareas" (Flutter)
// Uso: flutter create mis_tareas  →  reemplazar lib/main.dart por este archivo  →  flutter run
// También funciona pegándolo en https://dartpad.dev

import 'package:flutter/material.dart';

void main() => runApp(const MaterialApp(home: Tareas()));

class Tareas extends StatefulWidget {
  const Tareas({super.key});
  @override
  State<Tareas> createState() => _TareasState();
}

class _TareasState extends State<Tareas> {
  final _items = <String>[];
  final _ctrl = TextEditingController();

  void _agregar() {
    if (_ctrl.text.trim().isEmpty) return;
    setState(() => _items.add(_ctrl.text.trim()));
    _ctrl.clear();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Mis tareas')),
      body: Column(children: [
        TextField(controller: _ctrl, onSubmitted: (_) => _agregar()),
        Expanded(
          child: ListView.builder(
            itemCount: _items.length,
            itemBuilder: (_, i) => ListTile(title: Text(_items[i])),
          ),
        ),
      ]),
      floatingActionButton: FloatingActionButton(
        onPressed: _agregar, child: const Icon(Icons.add)),
    );
  }
}
