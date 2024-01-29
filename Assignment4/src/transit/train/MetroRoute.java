package transit.train;

import java.util.ArrayList;
import transit.core.Route;
import transit.core.Stop;
import transit.core.Vehicle;

public class MetroRoute extends Route
{
	public MetroRoute(int routeNum, String routeDesc, MetroStation first)
	{
		this.routeNumber = routeNum;
		this.routeDescription = routeDesc;
		this.firstStop = first;
		this.lastStop = first;
		this.vehicles = new ArrayList<Vehicle>();  	
	}


	@Override
	public void addDriver(String name, double speed) //Should I add three different cars to vehicles? or are the 3 cars one train?
	{
		Train newTrain = new Train(name, speed, 3, this); 
		vehicles.add(newTrain);
	}

	@Override
	public void addStop(String stopName, double x, double y) 
	{
		MetroStation newStop = new MetroStation(stopName, x, y);
		
		this.lastStop = newStop;

		Stop pointerStop = firstStop;
		
		while(pointerStop.nextStop != null)
		{
			pointerStop = pointerStop.nextStop;
		}
		
		pointerStop.nextStop = newStop;
		newStop.prevStop = pointerStop;
		this.lastStop = newStop;
	}
	
	public static void main(String[] args) 
	{
		// TODO Auto-generated method stub

	}

}
