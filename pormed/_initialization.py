import numpy

class ResInit():

	def __init__(self,DWOC,DGOC,gradw=0.433,grado=0.346,gradg=0.043,peow=0,peog=0):
		"""
		DWOC 	: Depth of Water-Oil-Contact
		DGOC 	: Depth of Gas-Oil-Contact

		gradw 	: water hydrostatic gradient, psi/ft
		grado 	: oil hydrostatic gradient, psi/ft
		gradg 	: gas hydrostatic gradient, psi/ft

		peow 	: capillary entry pressure for oil-water
		peog 	: capillary entry pressure for oil-gas
		"""

		self.DWOC = DWOC
		self.DGOC = DGOC

		self.gradw = gradw
		self.grado = grado
		self.gradg = gradg

		self.peow = peow
		self.peog = peog

	def waterpressure(self,depth):
		"""pressure of water phase at input depth"""
		return self.pwwoc+self.gradw*(depth-self.DWOC)

	def oilpressure(self,depth):
		"""pressure of oleic phase at input depth"""
		return self.pwwoc+self.peow+self.grado*(depth-self.DWOC)

	def gaspressure(self,depth):
		"""pressure of gas phase at input depth"""
		return self.pogoc+self.peog+self.gradg*(depth-self.DGOC)

	@property
	def pwwoc(self):
		"""water pressure at water-oil-contact"""
		return 14.7+self.gradw*self.DWOC

	@property
	def pwgoc(self):
		"""water pressure at gas-oil-contact"""
		return self.pwwoc+(self.DGOC-self.DWOC)*self.gradw

	@property
	def powoc(self):
		"""oil pressure at water-oil-contact"""
		return self.pwwoc+self.peow
	
	@property
	def pogoc(self):
		"""oil pressure at gas-oil-contact"""
		return self.oilpressure(self.DGOC)

	@property
	def pggoc(self):
		return self.gaspressure(self.DGOC)

	@property
	def FWL(self):
		"""free-water-level"""
		return self.DWOC+self.peow/(self.gradw-self.grado)

	def saturations(self,depth,pcow,pcog=None,pcgw=None):
		"""
		Zone1 	: below WOC; water
		Zone2 	: WOC to GOC; water and oil
		Zone3-a : GOC to transition; liquid and gas
		Zone3-b : above transition; water and gas

		pcow 	: oil-water capillary pressure model
		pcog 	: oil-gas capillary pressure model
		pcgw	: gas-water capillary pressure model
		"""

		depth = numpy.array(depth).flatten()

		Sw = numpy.ones(depth.shape)
		So = numpy.zeros(depth.shape)
		Sg = numpy.zeros(depth.shape)

		zone1 = depth>=self.DWOC
		zone2 = numpy.logical_and(depth<self.DWOC,depth>=self.DGOC)
		zone3 = depth<self.DGOC

		Sw2,So2 = self._water_oil_zone(depth[zone2],pcow)
		Sw3a,So3a,Sg3a = self._three_phase_zone(depth[zone3],pcow,pcog)
		Sw3b,Sg3b = self._water_gas_zone(depth[zone3],pcgw)

		Sw3 = numpy.zeros(Sw3a.shape)
		So3 = numpy.zeros(So3a.shape)
		Sg3 = numpy.zeros(Sg3b.shape)

		Sw3[So3a>=0] = Sw3a[So3a>=0]
		So3[So3a>=0] = So3a[So3a>=0]
		Sg3[So3a>=0] = Sg3a[So3a>=0]

		Sw3[So3a<0] = Sw3b[So3a<0]
		So3[So3a<0] = 0
		Sg3[So3a<0] = Sg3b[So3a<0]

		Sw[zone2] = Sw2
		Sw[zone3] = Sw3

		So[zone2] = So2
		So[zone3] = So3

		Sg[zone3] = Sg3

		return Sw,So,Sg

	def _water_oil_zone(self,depth,pcow):

		pw = self.waterpressure(depth)
		po = self.oilpressure(depth)

		Sw = pcow.idrainage(po-pw)

		return Sw,1-Sw

	def _three_phase_zone(self,depth,pcow,pcog):

		pw = self.waterpressure(depth)
		po = self.oilpressure(depth)
		pg = self.gaspressure(depth)

		Sl = pcog.idrainage(pg-po)
		Sw = pcow.idrainage(po-pw)

		return Sw,Sl-Sw,1-Sl

	def _water_gas_zone(self,depth,pcgw):

		pw = self.waterpressure(depth)
		pg = self.gaspressure(depth)

		Sw = pcgw.idrainage(pg-pw)

		return Sw,1-Sw


