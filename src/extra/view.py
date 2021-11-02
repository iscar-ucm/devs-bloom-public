from bokeh.io import output_notebook, show, output_file
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


class ScopeView:
  '''An scope'''

  @staticmethod
  def setFileOutput(filename):
    output_file(filename=filename)

  @staticmethod
  def setNotebookOutput():
    output_notebook()


  def __init__(self, title="Scope View", x_label="Time (s)", y_label="Value"):
    self.data_source = ColumnDataSource(data=dict(x=[0], y=[0]))
    self.figure = figure(plot_width=400, plot_height=400, x_range=(0,100),
      title=title, x_axis_label=x_label, y_axis_label=y_label)
    self.figure.step('x', 'y', source=self.data_source, line_width=2, color='red')

  def add(self, x, y):
    self.data_source.data['x'].append(x)
    self.data_source.data['y'].append(y)
  
  def show(self):
    show(self.figure)