package transit.core;

import java.util.ArrayList;

import transit.people.Passenger;

public abstract class Vehicle 
{
	protected String identifier;
	protected String driverName;
	protected double speed;
	protected double xCoordinate;
	protected double yCoordinate;
	protected Route route;
	public Stop currentDestination;
	protected ArrayList<Passenger> passengers;
	protected boolean isStopped;
	protected boolean isInbound;
	
	public void thankTheDriver()
	{
		System.out.println("Thank you for your hardwork " + driverName +"!");
	}
	
	public int letPassengersOff()
	{
		int counter = 0;
		
		ArrayList<Passenger> needOff = new ArrayList<Passenger>();
		
		for(Passenger person : passengers)
		{
			if (person.getDestination().stopNumber == currentDestination.stopNumber)
			{
				counter ++;
				currentDestination.passengersArrived.add(person);
				needOff.add(person);
			}
		}
		
		for(Passenger person : needOff)
		{
			if(passengers.contains(person))
			{
				passengers.remove(person);
			}
		}
		
		return counter;
	}
	
	public int letPassengersOn()
	{
		int capacity = getCapacity();
		if (currentDestination.passengersWaiting.size() > capacity)
		{
			for(int i = capacity-1; i >= 0 ; i--)
			{
				passengers.add(currentDestination.passengersWaiting.get(i));
			}
			
			currentDestination.losePassengers(capacity);
			
			return capacity;
		}
		else
		{
			int counter = 0;
			
			for(Passenger person : currentDestination.passengersWaiting)
			{
				counter ++;
				passengers.add(person);
			}
			
			currentDestination.passengersWaiting.clear();
			
			return counter;
		}
	}
	
	public abstract int getCapacity();
	
	public abstract double move(int minutes);
	
	public static void main(String[] args) 
	{
		// TODO Auto-generated method stub

	}

}
