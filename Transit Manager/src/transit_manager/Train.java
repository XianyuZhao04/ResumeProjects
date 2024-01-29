package transit_manager;

public class Train 
{
	//Fields!
	private String trainIdentifier;
	private String conductorName;
	private int cars;
	private int passengers;
	private double speed;
	private MetroRoute route;
	public MetroStation currentStation;
	
	
	//Constructor!
	public Train(String trainIdentifier, String conductorName, double speed, int cars, MetroRoute route)
	{
		this.trainIdentifier = trainIdentifier;
		this.conductorName = conductorName;
		this.cars = cars;
		this.speed = speed;
		this.route = route;
		this.currentStation = route.getFirstStop();
		
	}
	
	
	//Getters and Setters!
	public String getTrainIdentifier() //I don't think you should be able to change a bus identifier since you can't change
	{						 		 //your car's VIN number either. So no setter for this one.
	
		return trainIdentifier;
	}
	
	public String getConductorName() //since you can switch bus drivers or the driver can change names, let's make both.
	{
		return conductorName;
	}
	
	public void setConductorName(String newConductorName)
	{
		conductorName = newConductorName;
	}
	
	public int getCars() //The train cars can attach and detach I think, so I'll make both.
	{						 
		return cars;
	}
	
	public void setCars(int newCars)
	{
		cars = newCars;
	}
	
	public int getPassengers() //since the # of passengers definitely changes, let's make both.
	{
		return passengers;
	}
	
	public void setPassengers(int newPassengers)
	{
		passengers = newPassengers;
	}
	
	public double getSpeed() //since you can definitely change the speed of the bus, let's make both.
	{
		return speed;
	}
	
	public void setSpeed(double newSpeed)
	{
		speed = newSpeed;
	}
	
	public MetroRoute getRoute() //since the same bus can do different routes, let's make both.
	{
		return route;
	}
	
	public void setRoute(MetroRoute newRoute)
	{
		route = newRoute;
	}
	
	public MetroStation getCurrentStation() //since the bus stop can definitely change, let's make both.
	{
		return currentStation;
	}
	
	public void setCurrentStation(MetroStation newCurrentStation)
	{
		currentStation = newCurrentStation;
	}
	//End of Getters and Setters!!
	
	
	//Methods!
	public void thankTheConductor()
	{
		System.out.println("Thank you for your hardwork " + this.getConductorName());
	}
	
	public int calculateCapacity()
	{
		int capacity = cars * 120;
		return capacity;
	}
	
	public int letPassengersOff()
	{
		int passengersOff = passengers;
		passengers = 0;
		return passengersOff;
	}
		
	public int letPassengersOn()
	{
		int maxPassengersOn = this.calculateCapacity() - passengers;
		if (currentStation.getPassengersWaiting() <= maxPassengersOn)
		{
			int currentPassengers = currentStation.getPassengersWaiting();
			currentStation.losePassengers(currentPassengers);
			passengers += currentPassengers;
			return currentPassengers;
		}
		else
		{
			currentStation.losePassengers(maxPassengersOn);
			passengers += maxPassengersOn;
			return maxPassengersOn;
		}
		
	}
	
	public double moveToNextStation()
	{
		double totalDistance = route.calculateDistance();
		double totalTime = (totalDistance/speed);
		totalTime = totalTime*60;
		if (currentStation.equals(route.getFirstStop()))
		{
			MetroStation newStop = route.getLastStop();
			this.setCurrentStation(newStop);
		}
		else if (currentStation.equals(route.getLastStop()))
		{
			MetroStation newStop = route.getFirstStop();
			this.setCurrentStation(newStop);
		}
		return totalTime;
	}

	public String toString()
	{
		return "This is Train " + trainIdentifier + ", your conductor today is " + conductorName + ", you are currently on route number " + route.getRouteNumber() + ". Current station: " + currentStation.getStationName() + ". Number of Passengers: " + passengers +". Capacity: " + this.calculateCapacity();
	}

}
