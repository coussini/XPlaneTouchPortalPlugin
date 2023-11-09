class Pencil:
  def __init__(self, count):
    self._counter=count
  
  @property
  def counter(self):
    return self._counter
  
  @counter.setter
  def counter(self, count):
    self._counter = count

  @counter.getter
  def counter(self):
    return self._counter
  

HB = Pencil(100)
print(HB.counter)
HB.counter = 20
print(HB.counter)