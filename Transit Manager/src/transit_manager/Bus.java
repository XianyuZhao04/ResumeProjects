package transit_manager;

public class Bus 
{
	//Fields!
	private String busIdentifier;
	private String driverName;
	private int capacity;
	private int passengers;
	private double speed;
	private BusRoute route;
	public BusStop currentStop;
	
	
	//Constructor!
	public Bus(String busIdentifier, String driverName,double speed, BusRoute route)
	{
		this.busIdentifier = busIdentifier;
		this.driverName = driverName;
		this.speed = speed;
		this.route = route;
		this.currentStop = route.getFirstStop();
		capacity = 30;
		
	}
	
	
	//Getters and Setters!
	public String getBusIdentifier() //I don't think you should be able to change a bus identifier since you can't change
	{						 		 //your car's VIN number either. So no setter for this one.
	
		return busIdentifier;
	}
	
	public String getDriverName() //since you can switch bus drivers or the driver can change names, let's make both.
	{
		return driverName;
	}
	
	public void setDriverName(String newDriverName)
	{
		driverName = newDriverName;
	}
	
	public int getCapacity() //maybe the bus seats can sometimes break so that can cause the capacity to go down?
	{						 //So I'll make a setter for this one too
		return capacity;
	}
	
	public void setCapacity(int newCapacity)
	{
		capacity = newCapacity;
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
	
	public BusRoute getRoute() //since the same bus can do different routes, let's make both.
	{
		return route;
	}
	
	public void setRoute(BusRoute newRoute)
	{
		route = newRoute;
	}
	
	public BusStop getCurrentStop() //since the bus stop can definitely change, let's make both.
	{
		return currentStop;
	}
	
	public void setCurrentStop(BusStop newCurrentStop)
	{
		currentStop = newCurrentStop;
	}
	//End of Getters and Setters!!
	
	
	//Methods!
	public void thankTheDriver()
	{
		System.out.println("Thank you for your hardwork " + this.getDriverName());
	}
	
	public int letPassengersOff()
	{
		int passengersOff = passengers;
		passengers = 0;
		return passengersOff;
	}
		
	public int letPassengersOn()
	{
		int maxPassengersOn = capacity - passengers;
		if (currentStop.getPassengersWaiting() <= maxPassengersOn)
		{
			int currentPassengers = currentStop.getPassengersWaiting();
			currentStop.losePassengers(currentPassengers);
			passengers += currentPassengers;
			return currentPassengers;
		}
		else
		{
			currentStop.losePassengers(maxPassengersOn);
			passengers += maxPassengersOn;
			return maxPassengersOn;
		}
		
	}
	
	public double moveToNextStop()
	{
		double totalDistance = route.calculateDistance();
		double totalTime = (totalDistance/speed);
		totalTime = totalTime*60;
		if (currentStop.equals(route.getFirstStop()))
		{
			BusStop newStop = route.getLastStop();
			this.setCurrentStop(newStop);
		}
		else if (currentStop.equals(route.getLastStop()))
		{
			BusStop newStop = route.getFirstStop();
			this.setCurrentStop(newStop);
		}
		return totalTime;
	}

	public String toString()
	{
		return "This is Bus " + busIdentifier + ", your driver today is " + driverName + ", you are currently on route number " + route.getRouteNumber() + ". Current stop: " + currentStop.getStopName() + ". Number of Passengers: " + passengers +". Capacity: " + capacity;
	}


	
}
