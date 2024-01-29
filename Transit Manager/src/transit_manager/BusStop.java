package transit_manager;

public class BusStop 
{
	//Fields!!
	private String stopName;
	private int stopNumber;
	private double xCoordinate;
	private double yCoordinate;
	private int passengersWaiting;
	
	//Constructor!!
	public BusStop(String stopName, int stopNumber, double xCoordinate, double yCoordinate)
	{
		this.stopName = stopName;
		this.stopNumber = stopNumber;
		this.xCoordinate = xCoordinate;
		this.yCoordinate = yCoordinate;
	}
	
	//Getters and Setters!!
	public String getStopName() //Since the names of stops can change, let's do both.
	{
		return stopName;
	}
	
	public void setStopName(String newStopName)
	{
		stopName = newStopName;
	}
	
	public int getStopNumber() //Since the stop number can change because the route might get altered at some point, let's do both.
	{
		return stopNumber;
	}
	
	public void setStopNumber(int newStopNumber)
	{
		stopNumber = newStopNumber;
	}
	
	public double getXCoordinate() //Since the x coordinate of a stop doesn't change unless it's a whole new different stop with
	{						 	   //the same name, I'll only make a getter for this one
		return xCoordinate;
	}
	
	public double getYCoordinate() //Using the same logic as the x coordinate, I'll only make a getter for this one.
	{
		return yCoordinate;
	}
	
	public int getPassengersWaiting() //Since the # of passengers waiting per stop can change, let's make both.
	{
		return passengersWaiting;
	}
	
	public void setPassengersWaiting(int newPassengersWaiting)
	{
		passengersWaiting = newPassengersWaiting;
	}
	//End of Getters and Setters!!
	
	
	//Methods!
	public void gainPassengers()
	{
		double randomAddDouble =  5 + (Math.random()*30);
		int randomAddInt = (int) randomAddDouble;
		int newPassengersWaiting = passengersWaiting + randomAddInt;
		this.setPassengersWaiting(newPassengersWaiting);
	}
	
	public boolean losePassengers(int numPassengers)
	{
		int newPassWait = passengersWaiting - numPassengers;
		if (newPassWait < 0)
		{
			return false; //Operation failure??
		}
		else
		{
			this.setPassengersWaiting(newPassWait);
			return true; //Operation success??
		}
	}
	
	public double distance(BusStop other)
	{
		double totalDist = (Math.pow((other.getXCoordinate() - xCoordinate), 2)) + (Math.pow((other.getYCoordinate() - yCoordinate), 2));
		totalDist = Math.sqrt(totalDist);
		return totalDist;
		
	}
	
	public String toString()
	{
		return "This is Bus Stop " + stopName + " and it's number " + stopNumber + " on the route with the coordinates " + xCoordinate + ", " + yCoordinate + " with " + passengersWaiting + " passengers waiting";
	}
	//End of Methods!!
}