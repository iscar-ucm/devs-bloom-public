from numpy import array, dot, linalg, sin, cos
# from typing import Protocol

class USVController:

  def generate_trajectory(self) -> array:
    '''Compute a new target point'''

  def update_control(self) -> array:
    '''Compute the control action'''

  def update_position(self, x: array) -> None:
    '''Store an state update'''

  def add_waypoints(self, waypoints: list) -> None:
    '''Add one or more waypoints to the list'''

class USVPurePursuitController:
  '''A controller that guides the USV.'''

  def __init__(self) -> None:
    self.waypoints = []
    self.target = array([])
    self.v = 10
    self.L = 30
    self.u = array([0, 0])
    self.x = array([0, 0, 0])

  def generate_trajectory(self) -> array:
    '''Compute a new target point'''
    if len(self.waypoints) == 0:
      return None

    if len(self.waypoints) == 1:
      return self.waypoints[0]

    dr = array(self.waypoints[1]) - array(self.waypoints[0]) 
    v = dr / linalg.norm(dr)
    n = array([v[1], -v[0]])
    d = dot(self.waypoints[1], n) 
    r = array(self.x[0:2])
    target = r + (d - dot(r, n))*n + self.L*v
    distance = linalg.norm(array(self.waypoints[1]) - r)
    if distance < self.L and len(self.waypoints) > 2:
      self.waypoints.pop(0)
    return target

  def update_control(self) -> array:
    '''Compute the control action'''
    self.target = self.generate_trajectory()
    if self.target is None:
      return [0, 0]
    e = self.target - self.x[0:2]
    e_x = dot(e, array([cos(self.x[2]), sin(self.x[2])]))
    v = self.v if len(self.waypoints) > 2 else 0
    w = - v*2*e_x / (self.L**2)
    return [v, w]

  def update_position(self, x: array) -> None:
    '''Store an state update'''
    self.x = x

  def add_waypoints(self, waypoints: list) -> None:
    '''Add one or more waypoints to the list'''
    for w in waypoints:
      self.waypoints.append(w)
