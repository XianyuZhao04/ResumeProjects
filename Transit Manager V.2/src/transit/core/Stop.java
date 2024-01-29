package transit.core;

import java.util.ArrayList;

import transit.people.Passenger;

public abstract class Stop 
{
	protected String stopName;
	protected int stopNumber;
	protected double xCoordinate;
	protected double yCoordinate;
	protected ArrayList<Passenger> passengersWaiting;
	protected ArrayList<Passenger> passengersArrived;
	public Stop nextStop;
	public Stop prevStop;
	
	
	public ArrayList<Passenger> losePassengers(int numPassengers)
	{
		ArrayList<Passenger> passengersRemoved = new ArrayList<Passenger>();
		
		if(numPassengers > passengersWaiting.size())
		{
			return null;
		}
		else
		{
			for(int i = numPassengers ; i > 0 ; i--)
			{
				passengersRemoved.add(passengersWaiting.get(0));
				passengersWaiting.remove(0);
			}
			
			return passengersRemoved;
		}
	}
	
	public String toString()
	{
		return "This is stop " + stopName + " number " + stopNumber + ". Passengers Waiting: " + passengersWaiting.size() + ".";
	}
	
	public String getStopName()
	{
		return stopName;
	}
	
	public void setStopName(String newStopName)
	{
		this.stopName = newStopName;
	}
	
	public int getStopNum()
	{
		return stopNumber;
	}
	
	public void setStopNum(int newStopNum)
	{
		this.stopNumber = newStopNum;
	}
	
	public double getXCoord()
	{
		return xCoordinate;
	}
	
	public void setXCoord(double newXCoord)
	{
		this.xCoordinate = newXCoord;
	}
	
	public double getYCoord()
	{
		return yCoordinate;
	}
	
	public void setYCoord(double newYCoord)
	{
		this.yCoordinate = newYCoord;
	}
	
	public ArrayList<Passenger> getPassengersWaiting()
	{
		return passengersWaiting;
	}
	
	public void setPassengersWaiting(ArrayList<Passenger> newPassengersWaiting)
	{
		this.passengersWaiting = newPassengersWaiting;
	}
	
	public ArrayList<Passenger> getPassengersArrived()
	{
		return passengersArrived;
	}
	
	public abstract void gainPassengers();

	public static void main(String[] args) 
	{
		// TODO Auto-generated method stub

	}

}
