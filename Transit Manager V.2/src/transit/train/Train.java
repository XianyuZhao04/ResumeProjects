package transit.train;

import java.util.ArrayList;

import transit.core.Vehicle;
import transit.people.Passenger;

public class Train extends Vehicle 
{
	private int cars;
	
	public Train(String driver, double sp, int cars, MetroRoute rt, MetroStation stop, boolean isInbound)
	{
		this.identifier = "" + driver.hashCode();
		this.driverName = driver;
		this.speed = sp;
		this.xCoordinate = stop.getXCoord();
		this.yCoordinate = stop.getYCoord();
		this.route = rt;
		this.currentDestination = stop;
		this.isStopped = true;
		this.isInbound = isInbound;
		this.passengers = new ArrayList<Passenger>();
		this.cars = cars;
	}
	
	public Train(String driver, double sp, int cars, MetroRoute rt, MetroStation stop)
	{
		this.identifier = "" + driver.hashCode();
		this.driverName = driver;
		this.speed = sp;
		this.xCoordinate = stop.getXCoord();
		this.yCoordinate = stop.getYCoord();
		this.route = rt;
		this.currentDestination = stop;
		this.isStopped = true;
		this.isInbound = true;
		this.passengers = new ArrayList<Passenger>();
		this.cars = cars;
	}
	
	public Train(String driver, double sp, int cars, MetroRoute rt)
	{
		this.identifier = "" + driver.hashCode();
		this.driverName = driver;
		this.speed = sp;
		this.xCoordinate = ((MetroStation)rt.firstStop).getXCoord();	
		this.yCoordinate = ((MetroStation)rt.firstStop).getYCoord();
		this.route = rt;
		this.currentDestination = ((MetroStation)rt.firstStop);		
		this.isStopped = true;
		this.isInbound = true;
		this.passengers = new ArrayList<Passenger>();
		this.cars = cars;
	}

	@Override
	public int getCapacity() 
	{
		int capacity = cars * 120;
		return capacity;
	}

	@Override
	public double move(int minutes) 
	{
		
		if(isStopped == true)
		{
			letPassengersOn();
			isStopped = false;
			if(currentDestination == route.lastStop)
			{
				isInbound = false;
			}
			if(currentDestination == route.firstStop && isInbound == false)
			{
				isInbound = true;
			}
			
			if(isInbound == true)
			{
				currentDestination = currentDestination.nextStop;
			}
			else if(isInbound == false)
			{
				currentDestination = currentDestination.prevStop;
			}
		}
		
		double y2 = ((MetroStation)currentDestination).getYCoord();
		double x2 = ((MetroStation)currentDestination).getXCoord();
		double hypotenuse = Math.sqrt(Math.pow(y2 - this.yCoordinate, 2) + Math.pow(x2 - this.xCoordinate, 2));
		double speedInMin = speed/60;
		double totalDist = minutes*speedInMin;
		double ratio = totalDist/hypotenuse;
		
		if(hypotenuse>=totalDist)
		{
			this.xCoordinate = (1 - ratio)*(this.xCoordinate) + ratio*(x2);
			this.yCoordinate = (1 - ratio)*(this.yCoordinate) + ratio*(y2);
		}
		else
		{
			this.xCoordinate = x2;
			this.yCoordinate = y2;
			totalDist = hypotenuse;
		}
		
		if(this.xCoordinate == x2 && this.yCoordinate == y2)
		{
			this.isStopped = true;
			letPassengersOff();
		}
		
		return totalDist;
	}
	
	public String toString()
	{
		String stopped = "are";
		String inbound = "are";
		if (isStopped == false)
		{
			stopped = "are not";
		}
		if (isInbound == false)
		{
			inbound = "are not";
		}
		return "Train Identifier: " + identifier + ". Driver: " + driverName + ". Speed: " + speed + ". Coordinates: " + this.xCoordinate + "," + this.yCoordinate + ". Route Number: " + route.getRouteNumber() + ". Current Destination: " + currentDestination + ". We " + stopped + " stopped and we " + inbound + " inbound. Cars: " + cars + ". Passengers: " + passengers.size();
	}

	public static void main(String[] args) 
	{
		// TODO Auto-generated method stub

	}

}
