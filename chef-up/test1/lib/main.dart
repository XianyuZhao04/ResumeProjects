import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:latlong2/latlong.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:geolocator/geolocator.dart';
import 'package:url_launcher/url_launcher.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});
  static const trucks = [
      Marker(
        width: 30.0,
        height: 30.0,
        point: LatLng(40.444990, -79.940640),
        child: Icon(
          Icons.local_shipping,
          color: Colors.red,
          size: 30.0,
        )
      ),
      Marker(
        width: 30.0,
        height: 30.0,
        point: LatLng(40.444490, -79.943640),
        child: Icon(
          Icons.local_shipping,
          color: Colors.blue,
          size: 30.0,
        )
      ),
      Marker(
        width: 30.0,
        height: 30.0,
        point: LatLng(40.444019, -79.954590),
        child: Icon(
          Icons.local_shipping,
          color: Colors.purple,
          size: 30.0,
        )
      ),
      Marker(
        width: 30.0,
        height: 30.0,
        point: LatLng(40.445490, -79.942640),
        child: Icon(
          Icons.local_shipping,
          color: Colors.orange,
          size: 30.0,
        )
      ),
    ];

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ChefUp',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      home: const MyHomePage(title: 'ChefUp', trucks: trucks),
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({super.key, required this.title, this.trucks});

  final String title;
  final trucks;

  @override
  State<MyHomePage> createState() => _MyHomePageState(trucks: trucks);
}

class _MyHomePageState extends State<MyHomePage> {
  _MyHomePageState({this.trucks});
  final trucks;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        // TRY THIS: Try changing the color here to a specific color (to
        // Colors.amber, perhaps?) and trigger a hot reload to see the AppBar
        // change color while the other colors stay the same.
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        // Here we take the value from the MyHomePage object that was created by
        // the App.build method, and use it to set our appbar title.
        title: Text(widget.title),
      ),
      body: Container(
          decoration: BoxDecoration(
            image: DecorationImage(
              image: AssetImage('images/background.jpg'),
              fit: BoxFit.cover,
              colorFilter: ColorFilter.mode(
                Colors.black.withOpacity(0.75), // Adjust opacity as needed
                BlendMode.dstATop,
              ),
            )
          ),
          child: Center(
          // Center is a layout widget. It takes a single child and positions it
          // in the middle of the parent.
          child: Column(
            // Column is also a layout widget. It takes a list of children and
            // arranges them vertically. By default, it sizes itself to fit its
            // children horizontally, and tries to be as tall as its parent.
            //
            // Column has various properties to control how it sizes itself and
            // how it positions its children. Here we use mainAxisAlignment to
            // center the children vertically; the main axis here is the vertical
            // axis because Columns are vertical (the cross axis would be
            // horizontal).
            //
            // TRY THIS: Invoke "debug painting" (choose the "Toggle Debug Paint"
            // action in the IDE, or press "p" in the console), to see the
            // wireframe for each widget.
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              ElevatedButton(
                child: const Text('Trucker!'),
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => Truckview(title: "truck", trucks: trucks)),
                  );
                }
              ),

              Text("    "),

              ElevatedButton(
                child: const Text('User!'),
                onPressed: () {
                  // Navigate to second route when tapped.
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => Mapview(title: "map", trucks: trucks)),
                  );
                },
              ),
            ],
          ),
      ),
      )
    );
  }
}

class Truckview extends StatefulWidget {
  Truckview({super.key, required this.title, this.trucks});
  final String title;
  final trucks;

  @override
  State<Truckview> createState() => _Truckview(trucks: trucks);
}

class _Truckview extends State<Truckview> {
  _Truckview({this.trucks});
  final trucks;

  late bool servicePermission = false;
  late LocationPermission permission;
  @override
  Widget build(BuildContext context) {

    Future<Position> _getCurrentLocation() async {

      permission = await Geolocator.checkPermission();

      if(permission == LocationPermission.denied)
      {
        permission = await Geolocator.requestPermission();
      }
      return await Geolocator.getCurrentPosition();
    }

    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(widget.title),
      ),
      body: Center(
        child: Align(
          alignment: Alignment.center,
          child: ElevatedButton(
            child: const Text("Broadcast my Location"),
            onPressed: () {
              _getCurrentLocation().then((position) {
                trucks.add(
                  Marker(
                    point: LatLng(position.latitude, position.longitude), 
                    width: 30.0,
                    height: 30.0,
                    child: Icon(
                      Icons.local_shipping, color: Color.fromARGB(255, 136, 89, 1)
                    )
                  )
                );
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => Mapview(title: "map", trucks: trucks)),
                );
              });
            }
          )
        )
      )
    );
  }
}

class Mapview extends StatefulWidget {
  Mapview({super.key, required this.title, this.trucks});

  final String title;
  final trucks;

  @override
  State<Mapview> createState() => _Mapview(trucks: trucks);
}

class _Mapview extends State<Mapview> {
  LatLng userLocation = LatLng(40.443490, -79.941640);
  _Mapview({this.trucks});

  List<LatLng> routeCoordinates = [];
 
  // This is the method for getting a route
  Future<void> fetchRoute({
    required LatLng startLocation,
    required LatLng endLocation,
  }) async {
    // Start point and end point
    final LatLng startPoint = startLocation;
    final LatLng endPoint = endLocation;

    // This is the OSRM api for finding a route between two points
    final String apiUrl =
        'http://router.project-osrm.org/route/v1/driving/${startPoint.longitude},${startPoint.latitude};${endPoint.longitude},${endPoint.latitude}?geometries=geojson';

    // Get the response from OSRM server
    final Response<dynamic> response = await Dio().get(apiUrl);

    // Decode the response into a list of coordinates
    if (response.statusCode == 200) {
      final List<dynamic> coordinates = response.data['routes'][0]['geometry']['coordinates'];

      for (var coordinate in coordinates) {
        final double lat = coordinate[1];
        final double lng = coordinate[0];
        routeCoordinates.add(LatLng(lat, lng));
      }
    } else {
      throw Exception('Failed to fetch route');
    }
  }


  @override
  void initState() {
    super.initState();
  }
  final trucks;
  @override
  Widget build(BuildContext context) {
    return Scaffold(
    //Add Header if needed
  
      //Main Body for the Web, note that it is written as a column
      body: Column(
        //Direction of the column orientation
        verticalDirection: VerticalDirection.down,

          //Items in the column
        children: [
          //First item in the column, the flutter map
          Container(
            width:5000,
            height: 496,
            child: FlutterMap(
              
              options: const MapOptions(
                initialCenter: LatLng(40.443490, -79.941640),
                initialZoom: 17.2,
              ),
              children: [
                TileLayer(
                  urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                  userAgentPackageName: 'com.example.app',
                ),
                RichAttributionWidget(
                  attributions: [
                    TextSourceAttribution(
                      'OpenStreetMap contributors',
                      onTap: () => launchUrl(Uri.parse('https://openstreetmap.org/copyright')),
                    ),
                  ],
                ),
                MarkerLayer(
                  markers: [
                  Marker(point: userLocation, width: 30.0, height: 30.0, child: Icon(Icons.person)), ... trucks]
                ),
                Align(
                  alignment: Alignment.topLeft,
                  child: ElevatedButton(
                    child: const Text('Home'),
                    onPressed: () {
                      Navigator.pop(context);
                    }
                  ),
                ),
                PolylineLayer(
                    polylines: [
                      Polyline(
                        points: routeCoordinates,
                        color: Colors.blue,
                        strokeWidth: 3.0,
                      )
                    ],
                ),
              ],
            )
          ),


      //The "Menu" for all the food trucks with their pictures and title and descriptions.
      //Edit the containers to will
          Container(
            //Dimensions for the ListView
            width: double.infinity,
            height: 250,

            child: ListView(
              //Items in the ListView
              children: [

            ElevatedButton(
              onPressed: (){
                routeCoordinates.clear();
                fetchRoute(startLocation: userLocation, endLocation: trucks[0].point);
              },
              style: ButtonStyle(
                  backgroundColor: MaterialStatePropertyAll<Color>(Color.fromARGB(255, 215, 126, 23)),
                  minimumSize: MaterialStateProperty.all(Size(130, 40)),
                  elevation: MaterialStateProperty.all(0),
                  shape: MaterialStateProperty.all<RoundedRectangleBorder>(
                  RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20.0),)),
                  ),
              child: 
                Container(
                  padding: EdgeInsets.symmetric(vertical: 10),
                  width: 5000,
                  height: 100,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [ClipRRect(
                      borderRadius: BorderRadius.circular(100),
                      child: 
                        Image.network(
                          'images/burger.jpg')
                      ),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                            Text("Bob's Burgers!", style: const TextStyle(fontWeight: FontWeight.bold)), //Name of Food truck
                            Text("      "),
                            Text("Delicious and Quick! Come try us out today!") //Description of food truck
        ]
    )
]
          )
        )
      ),

            ElevatedButton(
              onPressed: (){
                routeCoordinates.clear();
                fetchRoute(startLocation: userLocation, endLocation: trucks[1].point);
              },
              style: ButtonStyle(
                  backgroundColor: MaterialStatePropertyAll<Color>(Color.fromARGB(255, 193, 152, 62)),
                  minimumSize: MaterialStateProperty.all(Size(130, 40)),
                  elevation: MaterialStateProperty.all(0),
                  shape: MaterialStateProperty.all<RoundedRectangleBorder>(
                  RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20.0),)),
                  ),
              child: 
                Container(
                  padding: EdgeInsets.symmetric(vertical: 10),
                  width: 5000,
                  height: 100,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [ClipRRect(
                      borderRadius: BorderRadius.circular(50),
                      child: 
                        Image.network('images/corndog.jpg')),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                            Text("Cassie's Corn Dogs", style: const TextStyle(fontWeight: FontWeight.bold)), //Name of Food truck
                            Text("      "),
                            Text("Pittsburgh's Authentic Korean Corn Dogs!") //Description of food truck
        ]
    )
]
          )
        )
      ),

            ElevatedButton(
              onPressed: (){
                routeCoordinates.clear();
                fetchRoute(startLocation: userLocation, endLocation: trucks[2].point);
              },
              style: ButtonStyle(
                  backgroundColor: MaterialStatePropertyAll<Color>(Color.fromARGB(255, 179, 176, 176)),
                  minimumSize: MaterialStateProperty.all(Size(130, 40)),
                  elevation: MaterialStateProperty.all(0),
                  shape: MaterialStateProperty.all<RoundedRectangleBorder>(
                  RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20.0),)),
                  ),
              child: 
                Container(
                  padding: EdgeInsets.symmetric(vertical: 10),
                  width: 5000,
                  height: 100,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [ClipRRect(
                      borderRadius: BorderRadius.circular(50),
                      child: 
                        Image.network('images/icecream.jpg')),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                            Text("Issac's Ice Cream", style: const TextStyle(fontWeight: FontWeight.bold)), //Name of Food truck
                            Text("      "),
                            Text("All the ice creams, all the flavors, we've got it!") //Description of food truck
        ]
    )
]
          )
        )
      ),

            ElevatedButton(
              onPressed: (){
                routeCoordinates.clear();
                fetchRoute(startLocation: userLocation, endLocation: trucks[3].point);
              },
              style: ButtonStyle(
                  backgroundColor: MaterialStatePropertyAll<Color>(Color.fromARGB(255, 192, 225, 84)),
                  minimumSize: MaterialStateProperty.all(Size(130, 40)),
                  elevation: MaterialStateProperty.all(0),
                  shape: MaterialStateProperty.all<RoundedRectangleBorder>(
                  RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20.0),)),
                  ),
              child: 
                Container(
                  padding: EdgeInsets.symmetric(vertical: 10),
                  width: 1000,
                  height: 100,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [ClipRRect(
                      borderRadius: BorderRadius.circular(50),
                      child: 
                        Image.network('images/taco.jpg')),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                            Text("Tony's Tacos      ", style: const TextStyle(fontWeight: FontWeight.bold)), //Name of Food truck
                            Text("Serving Tacos since 1988                                    ") //Description of food truck
        ]
    )
]
          )
        )
      ),


              ],
            ),
          )
        ]
      )
    );
  }
}