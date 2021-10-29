package view;

import extra.view.ScopeView;
import xdevs.core.modeling.Atomic;
import xdevs.core.modeling.Port;

public class ScopeSimple extends Atomic {
    public Port<Double> in = new Port<>("in");
    protected Double clock;
    protected ScopeView chart;
    protected String topTitle;

    public ScopeSimple(String name) {
        super(name);
        super.addInPort(in);
        chart = new ScopeView(name, name, "xTitle", "yTitle");
        chart.setMode(ScopeView.MODE.XYStep);
        chart.setXTitle("time");
        chart.setYTitle("values");
        chart.addSerie(name);
    }

    public void initialize() {
        clock = 0.0;
        super.passivate();
    }

    public void lambda() {
    }

    public void deltint() {
        clock += super.getSigma();
        super.passivate();
    }

    public void deltext(double e) {
        clock += e;
        Double y = (Double) in.getSingleValue();
        chart.add(clock, y, super.getName());
    }

    public void exit() {
    }

    public void setTitle(String title) {
        chart.setTitle(title);
    }

    public void setXTitle(String title) {
        chart.setXTitle(title);
    }

    public void setYTitle(String title) {
        chart.setYTitle(title);
    }
}
