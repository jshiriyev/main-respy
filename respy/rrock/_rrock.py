import sys

if __name__ == "__main__":
	# sys.path.append(r'C:\Users\javid.shiriyev\Documents\respy')
	sys.path.append(r'C:\Users\3876yl\Documents\respy')

import numpy

class ResRock():
	"""
	Base class that defines constant reservoir rock properties
	at the given pressure and temperature.
	"""

	def __init__(self,*args,poro=None,depth=None,comp=None,**kwargs):
		"""
		Initializes a reservoir rock with the following petrophysical parameters:
		
		poro    : porosity of the rock, dimensionless
		depth 	: depth of reservoir rock, ft
		comp 	: isothermal compressibility factor of rock, 1/psi
		
		*args and **kwargs goes to self.set_perm(*args,**kwargs)

		For any given pressure and temperature values.

		"""

		self._poro  = self.set_prop(poro)

		self._depth = self.set_prop(depth,0.3048)

		self._comp  = self.set_prop(comp,1/6894.76)

		self.set_perm(*args,**kwargs)

	def set_perm(self,xperm,*,yperm=None,zperm=None,yreduce:float=1.,zreduce:float=1.):
		"""Assigns the permeability values in mD to the grids.

		xperm 	: permeability in x-direction, mD
		yperm   : permeability in y direction, mD
		zperm   : permeability in z direction, mD

		yreduce : yperm to xperm ratio, dimensionless
		zreduce : zperm to xperm ratio, dimensionless

		"""

		self._xperm = self.set_prop(xperm,9.869233e-16)

		self._yperm = self._xperm*yreduce if yperm is None else self.set_prop(yperm,9.869233e-16)
		self._zperm = self._xperm*zreduce if zperm is None else self.set_prop(zperm,9.869233e-16)

	@property
	def poro(self):
		return self._poro

	@property
	def depth(self):
		if self._depth is not None:
			return self._depth/0.3048

	@property
	def comp(self):
		if self._comp is not None:
			return self._comp*6894.75729

	@property
	def xperm(self):
		if self._xperm is not None:
			return self._xperm/9.869233e-16

	@property
	def yperm(self):
		if self._yperm is not None:
			return self._yperm/9.869233e-16

	@property
	def zperm(self):
		if self._zperm is not None:
			return self._zperm/9.869233e-16

	@staticmethod
	def set_prop(prop,conv=1.):
		if prop is not None:
			return numpy.asarray(prop).astype(numpy.float_)*conv

if __name__ == "__main__":

	rrock = ResRock((10,15,20),poro=(0.1,0.2,0.3),yreduce=0.5,zreduce=0.1)

	print(rrock.xperm)
	print(rrock.yperm)
	print(rrock.zperm)
	print(rrock.poro)

