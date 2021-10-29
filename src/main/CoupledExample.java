package main;

import java.util.logging.Level;

import sensors.SensorExample;
import view.ScopeSimple;
import xdevs.core.modeling.Coupled;
import xdevs.core.simulation.Coordinator;
import xdevs.core.util.DevsLogger;

public class CoupledExample extends Coupled {
    public CoupledExample(String name) {
        super(name);
        SensorExample sensor = new SensorExample("Sensor", 5.0, 1.5);
        super.addComponent(sensor);
        ScopeSimple scope = new ScopeSimple("Scope");
        super.addComponent(scope);
        super.addCoupling(sensor.out, scope.in);
    }
    
    public static void main(String[] args) {
        DevsLogger.setup(Level.INFO);
        CoupledExample coupled = new CoupledExample("Example");
        Coordinator coordinator = new Coordinator(coupled);
        coordinator.initialize();
        coordinator.simulate(100.0);
        coordinator.exit();
    }
}
