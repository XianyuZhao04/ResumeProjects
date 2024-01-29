package transit.core;

import java.util.ArrayList;

public abstract class Route 
{
	protected int routeNumber;
	protected String routeDescription;
	public Stop firstStop;
	public Stop lastStop;
	protected ArrayList<Vehicle> vehicles;
	
	public void gainPassengersAll()
	{
		Stop currentStop = firstStop;
		
		while(currentStop != null)
		{
			currentStop.gainPassengers();
			currentStop = currentStop.nextStop;
		}
	}
	
	public int getRouteNumber() 
	{
		return routeNumber;
	}


	public void moveAll(int minutes)
	{
		int lastCar = vehicles.size();
		
		for(int i = 0 ; i < lastCar ; i++)
		{
			vehicles.get(i).move(minutes);
		}
	}
	
	
	
	public ArrayList<Vehicle> getVehicles() 
	{
		return vehicles;
	}
	
	public String toString()
	{
		String route = "This is route number " + routeNumber + ". Description: " + routeDescription + "\n";
		String stops = "";
		
		Stop currentStop = firstStop;
		while(currentStop != null)
		{
			stops += currentStop + "\n";
			currentStop = currentStop.nextStop;
		}
		return  route + stops + vehicles.toString() ;
	}


	public abstract void addDriver(String name, double speed);
	
	public abstract void addStop(String stopName, double x, double y);

	public static void main(String[] args) 
	{
		// TODO Auto-generated method stub

	}

}
