from dataclasses import dataclass

@dataclass
class Message:
  '''A simple message to transport measurements'''
  value: float
