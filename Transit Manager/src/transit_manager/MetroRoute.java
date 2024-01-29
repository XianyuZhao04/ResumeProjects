package transit_manager;

public class MetroRoute 
{
	//Fields!
	private int routeNumber;
	private String routeDescription;
	public MetroStation firstStop;
	public MetroStation lastStop;
	
	//Constructor!
	public MetroRoute(int routeNumber, String routeDescription, MetroStation firstStop, MetroStation lastStop)
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
	
	public MetroStation getFirstStop() //Since the stops can change, let's make both.
	{
		return firstStop;
	}
	
	public void setFirstStop(MetroStation newFirstStop)
	{
		firstStop = newFirstStop;
	}
	
	
	public MetroStation getLastStop() // Using the same logic as the one above, let's make both.
	{
		return lastStop;
	}
	
	public void setLastStop(MetroStation newLastStop)
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
