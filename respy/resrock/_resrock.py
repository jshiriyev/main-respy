class ResRock():
	"""
	Base class that defines constant reservoir rock properties
	at the given pressure and temperature.
	"""

	def __init__(self,poro=None,xperm=None,yperm=None,zperm=None,comp=None,depth=None):
		"""
        Initializes a reservoir rock with the following petrophysical parameters:

        poro    : porosity of the rock, dimensionless
        xperm   : permeability in x direction, mD
        yperm   : permeability in y direction, mD
        zperm   : permeability in z direction, mD
        comp 	: isothermal compressibility factor of rock, 1/psi
        depth 	: depth of reservoir, ft

        Returns the same parameters for any *args and **kwargs
        when called.
        """

		self._poro  = poro

		self._xperm = None if xperm is None else xperm*9.869233e-16
		self._yperm = None if yperm is None else yperm*9.869233e-16
		self._zperm = None if zperm is None else zperm*9.869233e-16

		self._comp  = None if comp is None else comp/6894.75729

		self._depth = None if depth is None else depth*0.3048

	def __call__(self,*args,**kwargs):

		return self

	@parameter
	def poro(self):
		return self._poro

	@parameter
	def xperm(self):
		if self._xperm is not None:
			return self._xperm/9.869233e-16

	@parameter
	def yperm(self):
		if self._yperm is not None:
			return self._yperm/9.869233e-16

	@parameter
	def zperm(self):
		if self._zperm is not None:
			return self._zperm/9.869233e-16

	@parameter
	def comp(self):
		if self._comp is not None:
			return self._comp*6894.75729

	@parameter
	def depth(self):
		if self._depth is not None:
			return self._depth/0.3048

