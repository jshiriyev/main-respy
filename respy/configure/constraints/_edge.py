import numpy

class Edge():
    """
    Represents the edges of reservoir in the simulator.
    """
    VALID_SORTS = {"press", "lrate", "orate", "wrate", "grate"}

    def __init__(self,face:str,*,start:float=0,stop:float=None,**kwargs):
        """
        Parameters
        ----------
        face    : boundary: xmin, xmax, ymin, ymax, zmin, or zmax

        start   : start time for implementing the boundary condition, days
        stop    : stop time for implementing the boundary condition, days

        **kwargs : dict
        Specifies the well constraint. Only one of the following should be provided:
        - 'press' : Constant bottom-hole pressure (psi)
        - 'lrate' : Constant liquid rate, (bbl/day)
        - 'orate' : Constant oil rate, (bbl/day)
        - 'wrate' : Constant water rate, (bbl/day)
        - 'grate' : Constant gas rate, (ft3/day)
        """
        self.face  = face

        self.start = start
        self.stop  = stop

        constraint  = {key:value for key,value in kwargs.items() if value is not None}

        if len(constraint)==1:
            self.sort,self.cond = next(iter(constraint.items()))
        elif len(constraint)>1:
            raise ValueError(f"Multiple edge conditions provided: {list(constraint.keys())}. Assign only one.")

    @property
    def face(self):
        """Getter for edge face in grids."""
        return self._face

    @face.setter
    def face(self,value:str):
        """Getter for edge face in grids."""
        self._face = value

    @property
    def axis(self):
        return self._face[0]

    @property
    def start(self):
        """Getter for well constraint start time."""
        return self._start/(24*60*60)

    @start.setter
    def start(self,value):
        """Setter for well constraint start time."""
        self._start = value*(24*60*60)

    @property
    def stop(self):
        """Getter for well constraint end time."""
        return None if self._stop is None else self._stop/(24*60*60)

    @stop.setter
    def stop(self,value):
        """Setter for well constraint end time."""
        self._stop = None if value is None else value*(24*60*60)

    @property
    def sort(self):
        """Getter for well constraint type."""
        return self._sort

    @sort.setter
    def sort(self,value):
        """Setter for edge constraint type. Ensures that the assigned value is in VALID_SORTS."""
        if value not in self.VALID_SORTS:
            raise ValueError(f"Invalid edge constraint type: {value}. Must be one of {self.VALID_SORTS}.")
        self._sort = value
    
    @property
    def cond(self):
        """Getter for well constraint value."""
        if self._sort == "press":
            return self._cond/6894.76
        elif self._sort in ("lrate","orate","wrate"):
            return self._cond*(24*60*60)/(0.3048**3)/5.615
        elif self._sort == "grate":
            return self._cond*(24*60*60)/(0.3048**3)

    @cond.setter
    def cond(self,value):
        """Setter for well constraint value."""
        if self._sort == "press":
            self._cond = value*6894.76
        elif self._sort in ("lrate","orate","wrate"):
            self._cond = value*(0.3048**3)/(24*60*60)*5.615
        elif self._sort == "grate":
            self._cond = value*(0.3048**3)/(24*60*60)

    @property
    def prod(self):
        """Getter for edge productivity array."""
        return self._prod*(3.28084**3)*(24*60*60)*6894.76

    @prod.setter
    def prod(self,value:numpy.ndarray):
        """Setter for edge productivity array."""
        self._prod = value/(3.28084**3)/(24*60*60)/6894.76
    

if __name__ == "__main__":

    bcond = Edge("xmin",press=500)

    print(bcond.cond)
    print(bcond.face)
    print(bcond.axis)
    print(bcond.sort)