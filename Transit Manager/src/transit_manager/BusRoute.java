package transit_manager;

public class BusRoute 
{
	//Fields!
	private int routeNumber;
	private String routeDescription;
	public BusStop firstStop;
	public BusStop lastStop;
	
	//Constructor!
	public BusRoute(int routeNumber, String routeDescription, BusStop firstStop, BusStop lastStop)
	{
		this.routeNumber = routeNumber;
		this.routeDescription = routeDescription;
		this.firstStop = firstStop;
		this.lastStop = lastStop;
	}
	
	//Getters and Setters!
	public int getRouteNumber() //Since the route number might change, let's make both.
	{
		return routeNumber;
	}
	
	public void setRouteNumber(int newRouteNumber)
	{
		routeNumber = newRouteNumber;
	}
	
	public String getRouteDescription() //Since the route description might get modified, let's make both.
	{
		return routeDescription;
	}
	
	public void setRouteDescription(String newRouteDescription)
	{
		routeDescription = newRouteDescription;
	}
	
	public BusStop getFirstStop() //Since the stops can change, let's make both.
	{
		return firstStop;
	}
	
	public void setFirstStop(BusStop newFirstStop)
	{
		firstStop = newFirstStop;
	}
	
	
	public BusStop getLastStop() // Using the same logic as the one above, let's make both.
	{
		return lastStop;
	}
	
	public void setLastStop(BusStop newLastStop)
	{
		lastStop = newLastStop;
	}
	//End of Getters and Setters!!
	
	
	//Methods!
	public double calculateDistance()
	{
		double totalDistance = firstStop.distance(lastStop);
		return totalDistance;
	}
	
	public String toString()
	{
		return "This is route number " + routeNumber + " Description: " + routeDescription;
	}

	

}
