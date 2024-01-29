package transit.people;

import transit.core.Stop;

public class Passenger 
{
	private String name;
	private Stop destination;
	public String[] nameArr = new String[] {"Adam","Bob","Carl","Dylan","Edward","Franklin","Gary","Howard","Issac","Jeremy","Kaylee","Linda","Michaela","Nancy","Olivia","Patty","Quinn","Rose","Vivian","Tina"};
	
	public Passenger(String name, Stop currentStop)
	{
		this.name = name;
		
		Stop tempStop = currentStop;
		int counter = 0;
		
		while(tempStop.prevStop != null)
		{
			tempStop = tempStop.prevStop;
		}
		
		while(tempStop != null)
		{
			counter ++;
			tempStop = tempStop.nextStop;
		}
		
		int randInt = 1 + (int)(Math.random() * ((counter - 1) + 1));
		
		tempStop = currentStop;
		
		while(tempStop.prevStop != null)
		{
			tempStop = tempStop.prevStop;
		}
		
		for(int i = 0 ; i < randInt ; i++)
		{
			this.destination = tempStop;
			tempStop = tempStop.nextStop;
		}
		
		if(this.destination.equals(currentStop))
		{
			if(this.destination.nextStop == null)
			{
				this.destination = this.destination.prevStop;
			}
			else
			{
				this.destination = this.destination.nextStop;
			}
		}
	}
	
	public Passenger(Stop currentStop)
	{
		int randomNum = (int)(Math.random() * ((19) + 1));
		this.name = nameArr[randomNum];
		
		Stop tempStop = currentStop;
		int counter = 0;
		
		while(tempStop.prevStop != null)
		{
			tempStop = tempStop.prevStop;
		}
		
		while(tempStop != null)
		{
			counter ++;
			tempStop = tempStop.nextStop;
		}
		
		int randInt = 1 + (int)(Math.random() * ((counter - 1) + 1));
		
		tempStop = currentStop;
		
		while(tempStop.prevStop != null)
		{
			tempStop = tempStop.prevStop;
		}
		
		for(int i = 0 ; i < randInt ; i++)
		{
			this.destination = tempStop;
			tempStop = tempStop.nextStop;
		}
		
		if(this.destination.equals(currentStop))
		{
			if(this.destination.nextStop == null)
			{
				this.destination = this.destination.prevStop;
			}
			else
			{
				this.destination = this.destination.nextStop;
			}
		}
	}
	
	public Stop getDestination()
	{
		return destination;
	}
	
	public String getName()
	{
		return name;
	}
	
	public String toString()
	{
		return "My name is " + name + " and I want to get off at " + destination + ".";
	}
	
	

	public static void main(String[] args) 
	{

	}

}
