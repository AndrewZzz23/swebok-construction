// Ejemplo práctico – "Mis tareas" (Flutter)
// Versión web publicada en el sitio: igual a la de la presentación, más un tema
// con fuente incluida y un texto de ayuda en el campo.

import 'package:flutter/material.dart';

void main() => runApp(MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: ThemeData(fontFamily: 'DM Sans', colorSchemeSeed: Colors.blue),
      home: const Tareas(),
    ));

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
        Padding(
          padding: const EdgeInsets.all(12),
          child: TextField(
            controller: _ctrl,
            decoration: const InputDecoration(hintText: 'Escribe una tarea y pulsa +'),
            onSubmitted: (_) => _agregar(),
          ),
        ),
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
