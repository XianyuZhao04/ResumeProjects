package transit.bus;

import java.util.ArrayList;

import transit.core.Vehicle;
import transit.people.Passenger;

public class Bus extends Vehicle 
{
	//Instance Variables
	private int capacity;
	
	//Constructors
	public Bus(String driver, double sp, BusRoute rt, BusStop stop, boolean isInbound)
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
		this.capacity = 35;
	}
	
	public Bus(String driver, double sp, BusRoute rt, BusStop stop)
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
		this.capacity = 35;
	}
	
	public Bus(String driver, double sp, BusRoute rt)
	{
		this.identifier = "" + driver.hashCode();
		this.driverName = driver;
		this.speed = sp;
		this.xCoordinate = ((BusStop)rt.firstStop).getXCoord();	
		this.yCoordinate = ((BusStop)rt.firstStop).getYCoord();
		this.route = rt;
		this.currentDestination = rt.firstStop;		
		this.isStopped = true;
		this.isInbound = true;
		this.passengers = new ArrayList<Passenger>();
		this.capacity = 35;
	}
	
	//Methods
	public int getCapacity() 
	{
		return capacity;
	}

	@Override
	public double move(int minutes)
	{
		double speedInMin = speed/60;
		double totalDist = 0;
		int count = 0;
		double leftOver = 0;
		
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
		
		for(int i = 0 ; i < minutes ; i++)
		{
			if(this.xCoordinate - ((BusStop)this.currentDestination).getXCoord() == 0)
			{
				break;
			}
			else if (this.xCoordinate - ((BusStop)this.currentDestination).getXCoord() > 0)
			{
				if (this.xCoordinate - ((BusStop)this.currentDestination).getXCoord() >= speedInMin)
				{
					this.xCoordinate -= speedInMin;
					totalDist += speedInMin;
					count ++;
				}
				else if (this.xCoordinate - ((BusStop)this.currentDestination).getXCoord() < speedInMin)
				{
					totalDist += this.xCoordinate - ((BusStop)this.currentDestination).getXCoord();
					leftOver = speedInMin - this.xCoordinate - ((BusStop)this.currentDestination).getXCoord();
					this.xCoordinate = ((BusStop)this.currentDestination).getXCoord();
					count ++;
					break;
				}
			}
			else if (this.xCoordinate - ((BusStop)this.currentDestination).getXCoord() < 0)
			{
				if ((this.xCoordinate - ((BusStop)this.currentDestination).getXCoord())*-1 >= speedInMin)
				{
					this.xCoordinate += speedInMin;
					totalDist += speedInMin;
					count ++;
				}
				else if ((this.xCoordinate - ((BusStop)this.currentDestination).getXCoord())*-1 < speedInMin)
				{
					totalDist += (this.xCoordinate - ((BusStop)this.currentDestination).getXCoord())*-1;
					leftOver = speedInMin - (this.xCoordinate - ((BusStop)this.currentDestination).getXCoord())*-1;
					this.xCoordinate = ((BusStop)this.currentDestination).getXCoord();
					count ++;
					break;
				}
			}
		}
		
		if(this.yCoordinate - ((BusStop)this.currentDestination).getYCoord() == 0)
		{
			;
		}
		else if (this.yCoordinate - ((BusStop)this.currentDestination).getYCoord() > 0)
		{
			if (this.yCoordinate - ((BusStop)this.currentDestination).getYCoord() >= leftOver)
			{
				this.yCoordinate -= leftOver;
				totalDist += leftOver;
			}
			else if (this.yCoordinate - ((BusStop)this.currentDestination).getYCoord() < leftOver)
			{
				totalDist += this.yCoordinate - ((BusStop)this.currentDestination).getYCoord();
				this.yCoordinate = ((BusStop)this.currentDestination).getYCoord();
			}
		}														///////////HERERERERERERE
		else if (this.yCoordinate - ((BusStop)this.currentDestination).getYCoord() < 0)
		{
			if ((this.yCoordinate - ((BusStop)this.currentDestination).getYCoord())*-1 >= leftOver)
			{
				this.yCoordinate += leftOver;
				totalDist += leftOver;
			}
			else if ((this.yCoordinate - ((BusStop)this.currentDestination).getYCoord())*-1 < leftOver)
			{
				totalDist += (this.yCoordinate - ((BusStop)this.currentDestination).getYCoord())*-1;
				this.yCoordinate = ((BusStop)this.currentDestination).getYCoord();
			}
		}
		
		for(int i = 0 ; i < minutes-count ; i ++)
		{
			if(this.yCoordinate - ((BusStop)this.currentDestination).getYCoord() == 0)
			{
				break;
			}
			else if (this.yCoordinate - ((BusStop)this.currentDestination).getYCoord() > 0)
			{
				if (this.yCoordinate - ((BusStop)this.currentDestination).getYCoord() >= speedInMin)
				{
					this.yCoordinate -= speedInMin;
					totalDist += speedInMin;
				}
				else if (this.yCoordinate - ((BusStop)this.currentDestination).getYCoord() < speedInMin)
				{
					totalDist += this.yCoordinate - ((BusStop)this.currentDestination).getYCoord();
					this.yCoordinate = ((BusStop)this.currentDestination).getYCoord();
					break;
				}
			}														///////////HERERERERERERE
			else if (this.yCoordinate - ((BusStop)this.currentDestination).getYCoord() < 0)
			{
				if ((this.yCoordinate - ((BusStop)this.currentDestination).getYCoord())*-1 >= speedInMin)
				{
					this.yCoordinate += speedInMin;
					totalDist += speedInMin;
				}
				else if ((this.yCoordinate - ((BusStop)this.currentDestination).getYCoord())*-1 < speedInMin)
				{
					totalDist += (this.yCoordinate - ((BusStop)this.currentDestination).getYCoord())*-1;
					this.yCoordinate = ((BusStop)this.currentDestination).getYCoord();
					break;
				}
			}
		}
			
		if(this.xCoordinate == ((BusStop)this.currentDestination).getXCoord() && this.yCoordinate == ((BusStop)this.currentDestination).getYCoord())
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
		return "Bus Identifier: " + identifier + ". Driver: " + driverName + ". Speed: " + speed + ". Coordinates: " + xCoordinate + "," + yCoordinate + ". Route Number: " + route.getRouteNumber() + ". Current Destination: " + currentDestination + ". We " + stopped + " stopped and we " + inbound + " inbound. Capacity: " + capacity + ". Passengers: " + passengers.size();
	}
}
