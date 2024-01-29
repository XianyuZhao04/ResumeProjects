package transit.train;

import java.util.ArrayList;

import transit.core.Stop;
import transit.people.Passenger;

public class MetroStation extends Stop
{
	public MetroStation(String name, double x, double y)
	{
		this.stopName = name;
		this.xCoordinate = x;
		this.yCoordinate = y;
		this.stopNumber = name.hashCode();
		this.nextStop = null;
		this.prevStop = null;
		this.passengersWaiting = new ArrayList<Passenger>(); 
		this.passengersArrived = new ArrayList<Passenger>(); 
	}
	
	public void gainPassengers() 
	{
		int gainPass = 1 + (int)(Math.random() * ((10 - 1) + 1));
		
		for (int i = 0 ; i < gainPass ; i++)
		{
			passengersWaiting.add(new Passenger(this));	
		}
	}

	public static void main(String[] args) 
	{

	}



}
