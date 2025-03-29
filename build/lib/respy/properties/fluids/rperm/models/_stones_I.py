import numpy as np

from ._brooks_corey import BrooksCorey

class StonesI():
    """
    This Model Provides IMBIBITION Relative Permeability MODELS for a THREE-PHASE system.
    
    """

    def __init__(self,
        swr     : float = 0.1,
        sor_ow  : float = 0.4,
        sor_go  : float = 0.4,
        sgr     : float = 0.05,
        k0rw    : float = 0.3,
        k0ro_ow : float = 0.8,
        k0ro_go : float = 0.8,
        k0rg    : float = 0.3,
        nw      : float = 2,
        no      : float = 2,
        ng      : float = 2,
        method  : str = "average",
        ):
        """Initializes the class.

        Parameters:
        ----------
        swr     = residual water saturation
        sor_ow  = residual oil saturtaion in oil-water system
        sor_go  = residual oil saturation in gas-oil system
        sgr     = criticial gas saturation

        k0rw    = water relative permeability at residual oil saturation in oil-water system
        k0ro_ow = oil relative permeability at residual water saturation in oil-water system
        k0ro_go = oil relative permeability at residual gas saturation in gas-oil system
        k0rg    = gas relative permeability at residual liquid saturation in gas-oil system

        nw      = water exponent on relative permeability curve
        no      = oil exponent on relative permeability curve
        ng      = gas exponent on relative permeability curve

        method  = som calculation method, defaults to average.

        """
        self.swr     = swr
        self.sor_ow  = sor_ow
        self.sor_go  = sor_go
        self.sgr     = sgr

        self.k0rw = k0rw
        self.k0ro_ow = k0ro_ow
        self.k0ro_go = k0ro_go
        self.k0rg = k0rg

        self.nw      = nw
        self.no      = no
        self.ng      = ng

        self.method  = method

    @property
    def slr_go(self):
        """Getter for the residual liquid saturation in gas-oil system."""
        return self.swr+self.sor_go

    @property
    def ow(self):
        """Shorter getter for the oil-water relative permeability model."""
        if not hasattr(self,"_oil_water"):
            self.oil_water = None

        return self._oil_water
    
    @property
    def oil_water(self):
        """Getter for the oil-water relative permeability model."""
        if not hasattr(self,"_oil_water"):
            self.oil_water = None

        return self._oil_water

    @oil_water.setter
    def oil_water(self,value):
        """Setter for the oil-water relative permeability model."""
        self._oil_water = BrooksCorey(self.swr,self.sor_ow,self.k0rw,self.k0ro_ow,self.nw,self.no)

    @property
    def go(self):
        """Shorter getter for the gas-oil relative permeability model."""
        if not hasattr(self,"_gas_oil"):
            self.gas_oil = None

        return self._gas_oil
    
    @property
    def gas_oil(self):
        """Getter for the gas-oil relative permeability model."""
        if not hasattr(self,"_gas_oil"):
            self.gas_oil = None

        return self._gas_oil

    @gas_oil.setter
    def gas_oil(self,value):
        """Setter for the gas-oil relative permeability model."""
        self._gas_oil = BrooksCorey(self.slr_go,self.sgr,self.k0ro_go,self.k0rg,self.no,self.ng)

    def swd(self,sw:np.ndarray):
        """Returns dimensionless water saturation."""
        values = (np.ravel(sw)-self.swr)/(1-self.swr-self.sor_ow)

        return np.clip(values,0,1)

    def sod(self,so:np.ndarray):
        """Returns dimensionless oil saturation."""
        values = (np.ravel(so)-self.sor_ow)/(1-self.swr-self.sor_ow-self.sgr)

        return np.clip(values,0,1)

    def sgd(self,sg:np.ndarray):
        """Returns dimensionless gas saturation."""
        values = (np.ravel(sg)-self.sgr)/(1-self.sgr-self.slr_go)

        return np.clip(values,0,1)

    def som(self,sg:np.ndarray=None):
        """Returns minimum oil saturation in three-phase system."""
        if self.method == "minimum":

            return np.min((self.sor_ow,self.sor_go))

        elif self.method == "average":

            if sg is None:
                raise ValueError("Gas saturation (sg) must be provided for 'average' method.")

            a = np.ravel(sg)/(1-self.swr-self.sor_go)

            return (1-a)*self.sor_ow+a*self.sor_go

        raise ValueError(f"Invalid method '{self.method}'. Choose from ['minimum', 'average'].")

    def sw_star(self,sw,som):
        """Returns dimensionless water saturation (starred)."""
        values = (np.ravel(sw)-self.swr)/(1-self.swr-som)

        return np.clip(values,0,1)

    def so_star(self,so,som):
        """Returns dimensionless oil saturation (starred)."""
        values = (np.ravel(so)-som)/(1-self.swr-som)

        return np.clip(values,0,1)

    def sg_star(self,sg,som):
        """Returns dimensionless gas saturation (starred)."""
        values = (np.ravel(sg))/(1-self.swr-som)

        return np.clip(values,0,1)

    def kro(self,sw,so,sg,kro_ow,kro_go):
        """Returns relative oil permeability based on Stone's Model I."""
        som = self.som(sg)

        sw_star = self.sw_star(sw,som)
        so_star = self.so_star(so,som)
        sg_star = self.sg_star(sg,som)

        beta = (so_star)/(1-sw_star)/(1-sg_star)

        return beta*(kro_ow*kro_go)/self.k0ro_ow
    
    def get(self,sw:np.ndarray,so:np.ndarray,sg:np.ndarray):
        """Computes three-phase relative permeabilities krw, kro and krg.

        Parameters:
        ----------
        sw : water saturation
        so : oil saturation
        sg : gas saturation

        """
        krw,kro_ow = self.ow.get(sw)
        kro_go,krg = self.go.get(sw+so)

        kro = self.kro(sw,so,sg,kro_ow,kro_go)

        sod = self.sod(so)

        kro[sod<0] = 0
        kro[sod>1] = self.k0ro_ow

        return krw,kro,krg

if __name__ == "__main__":

    # rp = StonesI(swr=0.1,sor_ow=0.4,sor_go=0.2,sgr=0.05,k0rw=0.3,k0ro_ow=0.8,k0ro_go=0.8,k0rg=0.3)

    # print(rp.get(0.3,0.5,0.2))

    rp = Stones(swr=0.15,sor_ow=0.15,sor_go=0.05,sgr=0.1,k0rw=0.3,k0ro_ow=0.88,k0ro_go=0.8,k0rg=0.3)

    print(rp.model_1(0.3,0.4,0.3,0.406,0.175))
    print(rp.model_2(0.030,0.406,0.175,0.035))