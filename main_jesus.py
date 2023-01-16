from time import perf_counter 
import edge.usv

def measured(f):
  def wrapper(*args, **kwargs):
    t_start = perf_counter()    
    f(*args, **kwargs)
    t_stop = perf_counter()
    print(f'The simulation ran in {t_stop-t_start} seconds')
  return wrapper

@measured
def test_one_usv(trajectory='rectangle', host='http://127.0.0.1:5000'):
  edge.usv.test_one_USV(trajectory, host)

@measured
def test_two_usv(trajectory='rectangle', host='http://127.0.0.1:5000'):
  edge.usv.test_two_USV(trajectory, host)

# Uncomment the tests you want to run
if __name__ == "__main__":
  test_one_usv(
    trajectory='rectangle',
    host='http://pc-iscar.dacya.ucm.es:5000'
  )
  # test_one_usv(trajectory='triangle')
  # test_two_usv(trajectory='rectangle')
  # test_two_usv(trajectory='triangle')
