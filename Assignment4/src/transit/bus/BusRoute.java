package transit.bus;

import java.util.ArrayList;
import transit.core.Route;
import transit.core.Stop;
import transit.core.Vehicle;

public class BusRoute extends Route 
{
	public BusRoute(int routeNum, String routeDesc, BusStop first)
	{
		this.routeNumber = routeNum;
		this.routeDescription = routeDesc;
		this.firstStop = first;
		this.lastStop = first;
		this.vehicles = new ArrayList<Vehicle>();  	
	}



	public void addDriver(String name, double speed)
	{
		Bus newBus = new Bus(name, speed, this); 
		vehicles.add(newBus);
	}


	public void addStop(String stopName, double x, double y) 
	{
		BusStop newStop = new BusStop(stopName, x, y);
		
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
