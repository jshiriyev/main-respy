import numpy as np

class VanGenuchten():

    def __init__(self,swr:float=0,sor:float=0,n:float=2,m:float=2,gamma:float=0.02):
        """
        The Van Genuchten (1980) model.

        Parameters:
        ----------
        swr    : irreducible water saturation
        sor    : residual oil saturation

        n, m, gamma   : empirical constants
        """

        self.swr = swr
        self.sor = sor

        self.n = n
        self.m = m

        self.gamma = gamma

    @property
    def imbibe(self):
        """Returns an instance of the Imbibition class."""
        return Imbibition(self.swr,self.sor,self.n,self.m,self.gamma)

class Imbibition(VanGenuchten):

    def __init__(self,*args,**kwargs):

        super().__init__(*args,**kwargs)

    def pc(self,sw):
        """Calculates capillary pressure from saturation.

        sw     : water saturation values

        """
        se = (np.ravel(sw)-self.swr)/(1-self.swr-self.sor)
        se = np.clip(se,0,1)

        return 1/self.gamma*(se**(-1/self.m)-1)**(1/self.n)

    def sw(self,pc):
        """Calculates saturation from capillary pressure, inverse calculations.

        pc     : capillary pressure values

        """
        se = ((self.gamma*pc)**self.n+1)**(-self.m)

        return self.swr+se*(1-self.swr-self.sor)

if __name__ == "__main__":

    import matplotlib.pyplot as plt

    ow = VanGenuchten(0.1,0.2,2,2,3.5)

    sw = np.linspace(0,1,1000)

    plt.semilogy(sw,ow.imbibe.pc(sw),label="Imbibition Curve")
    
    plt.vlines(0.1,1e-3,1e1,'k',linestyle='--',linewidth=1.)
    plt.vlines(0.8,1e-3,1e1,'k',linestyle='--',linewidth=1.)

    plt.xlim((0,1.))

    plt.legend()

    plt.show()