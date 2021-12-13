from xdevs import PHASE_ACTIVE, PHASE_PASSIVE, get_logger
from xdevs.models import Atomic, Port
import logging

logger = get_logger(__name__, logging.DEBUG)

class Input:
    '''Class that defines the input comming from a sensor'''

    def __init__(self, date, value, sensor_name):
        self.date = date
        self.value = value
        self.sensor_name = sensor_name

    def to_string(self):
        return "Input [value=" + self.value + ", sensor=" + self.sensor_name + ", Date=" + self.date + "]"

class FogServer(Atomic):    
    ''' A model for the fog server'''

    def __init__(self, name, period):
        self.i_sensor_01 = Port(Input, "i_sensor_01")
        self.add_in_port(self.i_sensor_01)
        self.i_sensor_01_values = []
        self.o_out = Port(Input, "o_out")
        self.add_out_port(self.o_out)

    def initialize(self):
        self.passivate()

    def exit(self):
        pass

    def lambdaf(self):
        self.o_out.add(self.input_values)

    def deltext(self, e):
        self.continuef(e)
        if (self.i_sensor_01.empty() == False): 
            self.i_sensor_01_values.append(self.i_sensor_01.get())


    protected Input currentInputNodovirtual2 = null;

    protected double processingTime;
    protected ArrayList<Input> listaInputs = new ArrayList<Input>();
    protected int contadorArray = 0;
    protected int contadorPrint = 0;
    protected File outputFile;
    protected Collection<Input> collection = null;
    public static ArrayList<Double> x_list = new ArrayList<Double>(); // Create an ArrayList object
	public static ArrayList<Double> y_list = new ArrayList<Double>(); // Create an ArrayList object
	public static ArrayList<Double> valores = new ArrayList<Double>(); // Create an ArrayList object
	double x0 = 13.0;
	double y0 = 80.0;
	protected int contadorKriging = 0;
	//########################################
	double krigingiInNodoVirtual1 = 0.0;
	double krigingiInNodoVirtual2 = 0.0;
	//########################################
    public FogServer(String name, double processingTime) {
        super(name);
        super.addInPort(iArrived);
        super.addInPort(iInNodoVirtual1);
        super.addInPort(iInNodoVirtual2);
        super.addInPort(iInNodoVirtual3);
        super.addInPort(iInNodoVirtual4);
        super.addInPort(iInNodoVirtual5);
        super.addInPort(iInNodoVirtual6);
        super.addInPort(iInNodoVirtual7);
        super.addInPort(iInNodoVirtual8);
        super.addInPort(iInNodoVirtual9);
        super.addInPort(iInNodoVirtual10);
        super.addInPort(iInNodoVirtual11);
        super.addInPort(iInNodoVirtual12);
        super.addInPort(iInNodoVirtual13);
        super.addInPort(iInNodoVirtual14);
        super.addInPort(iInNodoVirtual15);
        this.processingTime = processingTime;

        super.addOutPort(oOut);
        try {
            outputFile = new File("output.txt");
            if (outputFile.createNewFile()) {
                System.out.println("File created: " + outputFile.getName());
              } else {
                System.out.println("File already exists.");
              }
        }
        catch (IOException e) {
            System.out.println("An error occurred.");
            e.printStackTrace();
        }
      //########################################
        x_list.add(12.771);
        x_list.add(9.692);
        x_list.add(8.165);
        x_list.add(14.779);
        x_list.add(15.409);
        /*
        x_list.add(14.244);
        x_list.add(12.264);
        x_list.add(12.957);
        x_list.add(13.328);
        x_list.add(11.775);
        x_list.add(14.128);
        x_list.add(10.304);
        x_list.add(12.744);
        x_list.add(11.875);
		*/
        y_list.add(83.829);
        y_list.add(82.415);
        y_list.add(79.381);
        y_list.add(77.897);
        y_list.add(86.845);
        /*
        y_list.add(84.642);
        y_list.add(84.802);
        y_list.add(85.018);
        y_list.add(84.354);
        y_list.add(86.837);
        y_list.add(86.738);
        y_list.add(86.650);
        y_list.add(85.513);
        */
      //########################################
    }

    

    @Override
    public void deltint() {

    	List<Input> outliers = new ArrayList<Input>();
    	//File file = new File("output.txt");
	    
    	if(contadorArray >= 100) {

    		try {
    			//System.out.println("ListaInputs" + listaInputs.toString());
            	outliers = getOutliers(listaInputs);
    			System.out.println("outliers" + outliers.toString());
    			if(outliers.size() > 0) {
    				try {
    				double[] x = {0, 1, 2, 3, 4, 5, 6};
    			    double[] y = {listaInputs.get(listaInputs.size()-6).getRadiacion(), 
    			    		listaInputs.get(listaInputs.size()-5).getRadiacion(), 
    			    		listaInputs.get(listaInputs.size()-4).getRadiacion(), 
    			    		listaInputs.get(listaInputs.size()-3).getRadiacion(), 
    			    		listaInputs.get(listaInputs.size()-2).getRadiacion(), 
    			    		listaInputs.get(listaInputs.size()-1).getRadiacion(), 
    			    		listaInputs.get(listaInputs.size()).getRadiacion()};
    			    
    			    double[][] controls = new double[x.length][2];
    			       for (int i = 0; i < controls.length; i++) {
    			           controls[i][0] = x[i];
    			           controls[i][1] = y[i];
    			       }
    			       
    			       CubicSplineInterpolation1D spline = new CubicSplineInterpolation1D(x, y);
    			       double[][] zz = new double[61][2];
    			       for (int i = 0; i <= 60; i++) {
    			           zz[i][0] = i * 0.1;
    			           zz[i][1] = spline.interpolate(zz[i][0]);
    			       }
    			       
    			       RBFInterpolation1D rbf = new RBFInterpolation1D(x, y, new GaussianRadialBasis());
    			       double[][] ww = new double[61][2];
    			       for (int i = 0; i <= 60; i++) {
    			           ww[i][0] = i * 0.1;
    			           ww[i][1] = rbf.interpolate(zz[i][0]);
    			       }
    			       
    			       ShepardInterpolation1D shepard = new ShepardInterpolation1D(x, y, 3);
    			       double[][] vv = new double[61][2];
    			       for (int i = 0; i <= 60; i++) {
    			           vv[i][0] = i * 0.1;
    			           vv[i][1] = shepard.interpolate(zz[i][0]);
    			       }
    			       
    			       
    			       Input inputCubicSpline = new Input(listaInputs.get(listaInputs.size()).getDate(), zz[30][1], "CubicSpline");
    			       Input inputRBF = new Input(listaInputs.get(listaInputs.size()).getDate(), ww[30][1], "RBF");
    			       Input inputShepard = new Input(listaInputs.get(listaInputs.size()).getDate(), vv[30][1], "Shepard");

    			       processInput(inputCubicSpline);
    			       processInput(inputRBF);
    			       processInput(inputShepard);

    				}
    				catch(Exception e) {
    					System.out.println(e);
    				}
    			       
    			}
    			/*
        		FileWriter fr = new FileWriter(file, true);
        		BufferedWriter br = new BufferedWriter(fr);
        		PrintWriter pr = new PrintWriter(br);
            	for (int i = 0; i < outliers.size(); i++) {           		
            		pr.println(outliers.get(i).toString());
            	}
            	pr.println("Sep");
            	pr.close();
            	br.close();
            	fr.close();
            	*/
            	listaInputs.clear();
            	outliers.clear();
    		}
    		catch(Exception e) {
    			e.printStackTrace();
    		}
            contadorArray=0;
            contadorPrint++;
        }
        
        super.passivate();
        
    }

    @Override
    public void deltext(double e) {
    	if (super.phaseIs("passive")) {
        	//########################################
    		currentInputNodovirtual1 = iInNodoVirtual1.getSingleValue();
    		processInput(currentInputNodovirtual1);

    		currentInputNodovirtual2 = iInNodoVirtual2.getSingleValue();
    		processInput(currentInputNodovirtual2);
    		
        	if(currentInputNodovirtual1 != null) {
            	System.out.println("FogServer: " + currentInputNodovirtual1.toString());
            	processInput(currentInputNodovirtual1);
            	krigingiInNodoVirtual1 += currentInputNodovirtual1.getRadiacion();
        	}
        	
        	if(currentInputNodovirtual2 != null) {
            	System.out.println("FogServer: " + currentInputNodovirtual2.toString());
            	processInput(currentInputNodovirtual2);
            	krigingiInNodoVirtual2 += currentInputNodovirtual2.getRadiacion();
        	}
        	//########################################
        	contadorKriging++;
        	if(contadorKriging == 100) {
        		Input krigingInput;
        		double valor = 0.0;
        		double valorMedio = 0.0;
        		valores.add(krigingiInNodoVirtual1/100);
        		valores.add(krigingiInNodoVirtual2/100);
        		valores.add(77.0);
        		valores.add(85.0);
        		valores.add(70.0);
        		try {
        			valor = calculateKriging(x_list, y_list, valores, x0, y0);
            		//System.out.println("VALOR KRINGIN:" + valor );
        		}
        		catch(Exception e1) {
        			System.out.println(e1);
        			
        		}
        		double max = valores.get(0);
        		double min = valores.get(0);
        		for (int i= 0; i< valores.size(); i++) {
        			if(valores.get(i) < min) {
        				min = valores.get(i);
        			}
        			
        			if(valores.get(i) > max) {
        				max = valores.get(i);
        			}
        			
        		}
        		if(valor < max && valor > min) {
            		krigingInput = new Input(currentInputNodovirtual1.getDate(), valor, "kriging");
        		}
        		else {
        			//Si el valor no es acorde a lo esperado, reemplazarlo por la media del resto
        			for(int i=0; i < valores.size(); i++) {
        				valorMedio += valores.get(i);
        			}
        			valorMedio = valorMedio / (valores.size()-1); 
            		krigingInput = new Input(currentInputNodovirtual1.getDate(), valorMedio, "krigingCorregido");
        		}
        		processInput(krigingInput);
        		contadorKriging=0;
        	}
            super.passivate();
            super.holdIn("active", 0);
        }
    }

    @Override
    public void lambda() {
    	oOut.addValues(listaInputs);
        //oOut.addValue(currentInput);
    }
    
    
    //Calculo Outliers http://www.mathwords.com/o/outlier.htm
    public static List<Input> getOutliers(List<Input> input) {
        List<Input> output = new ArrayList<Input>();
        List<Input> data1 = new ArrayList<Input>();
        List<Input> data2 = new ArrayList<Input>();
        if (input.size() % 2 == 0) {
            data1 = input.subList(0, input.size() / 2);
            //System.out.println("data1: " + data1.toString());
            data2 = input.subList(input.size() / 2, input.size());
            //System.out.println("data2: " + data2.toString());

        }
        else {
            data1 = input.subList(0, input.size() / 2);
            data2 = input.subList(input.size() / 2 + 1, input.size());
        }
        double q1 = getMedian(data1);
        //System.out.println("q1: " + q1);
        double q3 = getMedian(data2);
        //System.out.println("q3: " + q3);

        double iqr = q3 - q1;       
        if(iqr < 0) {
        	iqr = -iqr;
        }
        //System.out.println("iqr: " + iqr);

        double lowerFence = q1 - 1.5 * iqr;
        //System.out.println("lowerFence: " + lowerFence);

        double upperFence = q3 + 1.5 * iqr;
        //System.out.println("upperFence: " + upperFence);

        for (int i = 0; i < input.size(); i++) {
        	//System.out.println(input.get(i).toString());
            if (input.get(i).getRadiacion() < lowerFence || input.get(i).getRadiacion() > upperFence) {
            	output.add(input.get(i));
                //System.out.println("Oulier: " + input.get(i).toString());
            }
                
        }
        return output;
    }
    
    private static double getMedian(List<Input> data) {
        if (data.size() % 2 == 0)
            return (data.get(data.size() / 2).getRadiacion() + data.get(data.size() / 2 - 1).getRadiacion()) / 2;
        else
            return data.get(data.size() / 2).getRadiacion();
    }
    
    private void processInput(Input currentInput) {
        if(currentInput != null) {
        	//System.out.println("Input recibido" + currentInput.toString());
            listaInputs.add(contadorArray,currentInput);
            contadorArray++;
        }
    }
    
