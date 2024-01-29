package transit_manager;

public class MetroStation 
{

	//Fields!!
	private String stationName;
	private int stationNumber;
	private double xCoordinate;
	private double yCoordinate;
	private int passengersWaiting;
		
	//Constructor!!
	public MetroStation(String stationName, int stationNumber, double xCoordinate, double yCoordinate)
	{
		this.stationName = stationName;
		this.stationNumber = stationNumber;
		this.xCoordinate = xCoordinate;
		this.yCoordinate = yCoordinate;
	}
	
	//Getters and Setters!!
	public String getStationName() //Since the names of stops can change, let's do both.
	{
		return stationName;
	}
	
	public void setStationName(String newStationName)
	{
		stationName = newStationName;
	}
	
	public int getStationNumber() //Since the stop number can change because the route might get altered at some point, let's do both.
	{
		return stationNumber;
	}
	
	public void setStationNumber(int newStationNumber)
	{
		stationNumber = newStationNumber;
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
		double randomAddDouble =  20 + (Math.random()*200);
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
	
	public double distance(MetroStation other)
	{
		double totalDist = (Math.pow((other.getXCoordinate()-xCoordinate), 2)) + (Math.pow((other.getYCoordinate()-yCoordinate), 2));
		totalDist = Math.sqrt(totalDist);
		return totalDist;
		
	}
	
	public String toString()
	{
		return "This is Train Station " + stationName + " and it's number " + stationNumber + " on the route with the coordinates " + xCoordinate + ", " + yCoordinate + " with " + passengersWaiting + " passengers waiting";
	}
	//End of Methods!!
}