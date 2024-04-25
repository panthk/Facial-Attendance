import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:http/http.dart' as http;

class BackendBloc extends Cubit<String> {
  BackendBloc() : super('');

  Future<void> fetchData() async {
    final response = await http.get(Uri.parse('http://localhost:5000/api/data'));
    if (response.statusCode == 200) {
      emit(response.body);
    } else {
      emit('Failed to fetch data');
    }
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: BlocProvider(
        create: (context) => BackendBloc(),
        child: MyWidget(),
      ),
    );
  }
}

class MyWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final backendBloc = BlocProvider.of<BackendBloc>(context);

    return Scaffold(
      appBar: AppBar(
        title: Text('Flutter App with Python Backend'),
      ),
      body: Center(
        child: ElevatedButton(
          onPressed: () {
            backendBloc.fetchData();
          },
          child: Text('Fetch Data from Python Backend'),
        ),
      ),
    );
  }
}

class MyWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final backendBloc = BlocProvider.of<BackendBloc>(context);

    return Scaffold(
      // ... (previous widget code remains the same)

      body: Center(
        child: BlocBuilder<BackendBloc, String>(
          builder: (context, state) {
            return Text(state);
          },
        ),
      ),
    );
  }
}

