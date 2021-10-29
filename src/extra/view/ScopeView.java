package extra.view;

import java.awt.Color;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.util.HashMap;
import javax.swing.JFrame;

import org.jfree.chart.ChartFactory;
import org.jfree.chart.ChartPanel;
import org.jfree.chart.JFreeChart;
import org.jfree.chart.plot.PlotOrientation;
import org.jfree.chart.renderer.xy.XYItemRenderer;
import org.jfree.chart.renderer.xy.XYStepRenderer;
import org.jfree.data.xy.XYSeries;
import org.jfree.data.xy.XYSeriesCollection;
import org.jfree.ui.RefineryUtilities;

public class ScopeView extends JFrame {
	private static final long serialVersionUID = 1L;
	public static enum MODE {XYLine, XYStep};
	
	private HashMap<String,XYSeries> seriesMap;	// Series JFreeChart.
	private XYSeriesCollection dataSet;			// Almacenamiento de datos.
	private JFreeChart chart;
	protected MODE mode;

	public ScopeView(String topTitle, String title, String xTitle, String yTitle) {
		super(topTitle);

		mode = MODE.XYLine;
		seriesMap = new HashMap<String,XYSeries>();
        dataSet = new XYSeriesCollection();
    	chart = ChartFactory.createXYLineChart(title, xTitle, yTitle, dataSet, PlotOrientation.VERTICAL, true, true, false);
        chart.setBackgroundPaint(Color.white);

        ChartPanel chartPanel = new ChartPanel(chart);
        chartPanel.setPreferredSize(new java.awt.Dimension(500, 270));
        chartPanel.setMouseZoomable(true, false);
        setContentPane(chartPanel);
        addWindowListener(new WindowAdapter() {
            public void windowClosing(WindowEvent e) {
              dispose();
            }
          });
        super.pack();
        //super.setTitle(topTitle);
        RefineryUtilities.centerFrameOnScreen(this);
        this.setVisible(true);
	}
	
	public void addSerie(String serieName) {
		if(seriesMap.containsKey(serieName)) return;
		XYSeries serie = new XYSeries(serieName);
		seriesMap.put(serieName, serie);
		dataSet.addSeries(serie);
	}

    public void add(double x, double y, String serieName) {
    	seriesMap.get(serieName).add(x, y);
    }

    public void add(Double x, Double y, String serieName) {
    	seriesMap.get(serieName).add(x, y);
    }

    public void add(double x, double[] y, String serieName) {
    	for(int i=0; i<y.length; ++i)
    		seriesMap.get(serieName + "[" + i + "]").add(x, y[i]);
    }

    public void add(Double x, Double[] y, String serieName) {
    	for(int i=0; i<y.length; ++i)
    		seriesMap.get(serieName + "[" + i + "]").add(x, y[i]);
    }

    public void setTitle(String title) {
		chart.setTitle(title);
	}

	public void setXTitle(String title) {
		chart.getXYPlot().getDomainAxis().setLabel(title);
	}

	public void setYTitle(String title) {
		chart.getXYPlot().getRangeAxis().setLabel(title);
	}

	public void setMode(MODE mode) {
		this.mode = mode;
		XYItemRenderer renderer = null;
		if(mode.equals(MODE.XYStep))
			renderer = new XYStepRenderer();
		chart.getXYPlot().setRenderer(renderer);
	}
    
}
