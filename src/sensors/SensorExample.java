package sensors;

import xdevs.core.modeling.Atomic;
import xdevs.core.modeling.Port;

/**
 * Example of Sensor implementation. We still need to add an external file to read data from.
 * However, this is an initial examen to be discussed in our next meeting.
 */

public class SensorExample extends Atomic {
    protected Double start;
    protected Double period;
    public Port<Double> out = new Port<>("out");

    public SensorExample(String name, Double start, Double period) {
        super(name);
        super.addOutPort(out);
        this.start = start;
        this.period = period;
    }

    @Override
    public void initialize() {
        super.holdIn("active", start);        
    }

    @Override
    public void lambda() {
        // Let's send a random number, that's all:
        Double value = Math.random();
        out.addValue(value);
    }

    @Override
    public void deltint() {
        super.holdIn("active", period);        
    }

    @Override
    public void deltext(double e) {
        // We should not reach this funcion right now.
        super.passivate();        
    }

    @Override
    public void exit() { }

}