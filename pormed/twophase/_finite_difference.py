import matplotlib.pyplot as plt
import numpy as np

from scipy.sparse import csr_matrix as csr
from scipy.sparse import diags

from scipy.sparse.linalg import spsolve as sps

# import fluids

# from borepy.items import PorRock
# from borepy.items import Wells

from ._relperm import RelPerm

from ._cappres import BrooksCorey
from ._cappres import VanGenuchten
from ._cappres import JFunction
from ._cappres import ScanCurves

class TwoPhaseIMPES():
    
    def __init__(self,res,fluids,wells,relperm):

        self.PorRock = PorRock("rectangle")()

        # There can be two slightly compressible fluids where the
        # second one is at irreducible saturation, not mobile

        self.Fluids = Fluids(number=2)

        self.Wells = Wells()

        self.rp = relperm

    def set_transmissibility(self):

        dx0 = self.res.grid_sizes[:,0]
        dy0 = self.res.grid_sizes[:,1]
        dz0 = self.res.grid_sizes[:,2]

        dxm = self.res.grid_sizes[self.res.grid_indices[:,1],0]
        dxp = self.res.grid_sizes[self.res.grid_indices[:,2],0]
        dym = self.res.grid_sizes[self.res.grid_indices[:,3],1]
        dyp = self.res.grid_sizes[self.res.grid_indices[:,4],1]
        dzm = self.res.grid_sizes[self.res.grid_indices[:,5],2]
        dzp = self.res.grid_sizes[self.res.grid_indices[:,6],2]

        Ax = self.res.grid_areas[:,0]
        Ay = self.res.grid_areas[:,1]
        Az = self.res.grid_areas[:,2]

        kx0 = self.res.permeability[:,0]
        ky0 = self.res.permeability[:,1]
        kz0 = self.res.permeability[:,2]

        kxm = self.res.permeability[self.res.grid_indices[:,1],0]
        kxp = self.res.permeability[self.res.grid_indices[:,2],0]
        kym = self.res.permeability[self.res.grid_indices[:,3],1]
        kyp = self.res.permeability[self.res.grid_indices[:,4],1]
        kzm = self.res.permeability[self.res.grid_indices[:,5],2]
        kzp = self.res.permeability[self.res.grid_indices[:,6],2]

        dxm_mean = (dx0+dxm)/2
        dxp_mean = (dx0+dxp)/2
        dym_mean = (dy0+dym)/2
        dyp_mean = (dy0+dyp)/2
        dzm_mean = (dz0+dzm)/2
        dzp_mean = (dz0+dzp)/2

        kxm_mean = (2*dxm_mean)/(dx0/kx0+dxm/kxm)
        kxp_mean = (2*dxp_mean)/(dx0/kx0+dxp/kxp)
        kym_mean = (2*dym_mean)/(dy0/ky0+dym/kym)
        kyp_mean = (2*dyp_mean)/(dy0/ky0+dyp/kyp)
        kzm_mean = (2*dzm_mean)/(dz0/kz0+dzm/kzm)
        kzp_mean = (2*dzp_mean)/(dz0/kz0+dzp/kzp)

        self.TXM = (Ax*kxm_mean)/(dxm_mean)
        self.TYM = (Ay*kym_mean)/(dym_mean)
        self.TZM = (Az*kzm_mean)/(dzm_mean)

        self.TXP = (Ax*kxp_mean)/(dxp_mean)
        self.TYP = (Ay*kyp_mean)/(dyp_mean)
        self.TZP = (Az*kzp_mean)/(dzp_mean)

    def set_wells(self):

        self.well_grids      = np.array([],dtype=int)
        self.well_indices    = np.array([],dtype=int)
        self.well_bhpflags   = np.array([],dtype=bool)
        self.well_limits     = np.array([],dtype=float)
        self.well_waterflags = np.array([],dtype=bool)
        self.well_oilflags   = np.array([],dtype=bool)

        wells = zip(self.wells.tracks,self.wells.consbhp,self.wells.limits,self.wells.water,self.wells.oil)

        for index,(track,flag,limit,water,oil) in enumerate(wells):

            ttrack = np.transpose(track[:,:,np.newaxis],(2,1,0))

            vector = self.res.grid_centers[:,:,np.newaxis]-ttrack

            distance = np.sqrt(np.sum(vector**2,axis=1))

            well_grid = np.unique(np.argmin(distance,axis=0))

            well_index = np.full(well_grid.size,index,dtype=int)
    
            well_bhpflag = np.full(well_grid.size,flag,dtype=bool)

            well_limit = np.full(well_grid.size,limit,dtype=float)

            well_waterflag = np.full(well_grid.size,water,dtype=bool)
            
            well_oilflag = np.full(well_grid.size,oil,dtype=bool)

            self.well_grids = np.append(self.well_grids,well_grid)

            self.well_indices = np.append(self.well_indices,well_index)

            self.well_bhpflags = np.append(self.well_bhpflags,well_bhpflag)

            self.well_limits = np.append(self.well_limits,well_limit)

            self.well_waterflags = np.append(self.well_waterflags,well_waterflag)

            self.well_oilflags = np.append(self.well_oilflags,well_oilflag)

        dx = self.res.grid_sizes[self.well_grids,0]
        dy = self.res.grid_sizes[self.well_grids,1]
        dz = self.res.grid_sizes[self.well_grids,2]

        req = 0.14*np.sqrt(dx**2+dy**2)

        rw = self.wells.radii[self.well_indices]

        skin = self.wells.skinfactors[self.well_indices]

        kx = self.res.permeability[:,0][self.well_grids]
        ky = self.res.permeability[:,1][self.well_grids]

        dz = self.res.grid_sizes[:,2][self.well_grids]

        self.JR = (2*np.pi*dz*np.sqrt(kx*ky))/(np.log(req/rw)+skin)

    def set_time(self,step,total):

        self.time_step = step
        self.time_total = total

        self.time_array = np.arange(self.time_step,self.time_total+self.time_step,self.time_step)

    def initialize(self,pressure,saturation):

        N = self.time_array.size

        self.pressure = np.empty((self.res.grid_numtot,N+1))
        self.pressure[:,0] = pressure

        self.Sw = np.empty((self.res.grid_numtot,N+1))
        self.Sw[:,0] = saturation

        # for index,(p,sw) in enumerate(zip(self.pressure[:,-1],self.Sw[:,-1])):
        #   print("{:d}\tP\t{:3.0f}\tSw\t{:.4f}".format(index,p,sw))

    def solve(self):

        Vp = self.res.grid_volumes*self.res.porosity

        muw = self.fluids.viscosity[0]
        muo = self.fluids.viscosity[1]
        
        fvfw = self.fluids.fvf[0]
        fvfo = self.fluids.fvf[1]
        
        cr = self.res.compressibility

        cw = self.fluids.compressibility[0]
        co = self.fluids.compressibility[1]

        wflow_1phase = ~np.logical_and(self.well_waterflags,self.well_oilflags)

        sp_wf = np.logical_and(self.well_waterflags,wflow_1phase)
        sp_of = np.logical_and(self.well_oilflags,wflow_1phase)

        cpw = np.logical_and(self.well_bhpflags,self.well_waterflags)
        cpo = np.logical_and(self.well_bhpflags,self.well_oilflags)

        cqw = np.logical_and(~self.well_bhpflags,self.well_waterflags)
        cqo = np.logical_and(~self.well_bhpflags,self.well_oilflags)

        cxm_0 = self.res.grid_indices[self.res.grid_hasxmin,0]
        cxm_m = self.res.grid_indices[self.res.grid_hasxmin,1]

        cxp_0 = self.res.grid_indices[self.res.grid_hasxmax,0]
        cxp_p = self.res.grid_indices[self.res.grid_hasxmax,2]

        cym_0 = self.res.grid_indices[self.res.grid_hasymin,0]
        cym_m = self.res.grid_indices[self.res.grid_hasymin,3]

        cyp_0 = self.res.grid_indices[self.res.grid_hasymax,0]
        cyp_p = self.res.grid_indices[self.res.grid_hasymax,4]

        czm_0 = self.res.grid_indices[self.res.grid_haszmin,0]
        czm_m = self.res.grid_indices[self.res.grid_haszmin,5]

        czp_0 = self.res.grid_indices[self.res.grid_haszmax,0]
        czp_p = self.res.grid_indices[self.res.grid_haszmax,6]

        mshape = (self.res.grid_numtot,self.res.grid_numtot)
        vshape = (self.res.grid_numtot,1)

        vzeros = np.zeros(len(self.wells.itemnames),dtype=int)

        krw,kro = self.rp.water_oil(Sw=self.Sw[:,0])

        krw_xm = krw[cxm_0]
        krw_xp = krw[cxp_0]
        krw_ym = krw[cym_0]
        krw_yp = krw[cyp_0]
        krw_zm = krw[czm_0]
        krw_zp = krw[czp_0]

        kro_xm = kro[cxm_0]
        kro_xp = kro[cxp_0]
        kro_ym = kro[cym_0]
        kro_yp = kro[cyp_0]
        kro_zm = kro[czm_0]
        kro_zp = kro[czp_0]

        for index,time in enumerate(self.time_array):

            print("@{:5.1f}th time step".format(time))

            d11 = (Vp*self.Sw[:,index])/(self.time_step*fvfw)*(cr+cw)
            d12 = (Vp)/(self.time_step*fvfw)
            d21 = (Vp*(1-self.Sw[:,index]))/(self.time_step*fvfo)*(cr+co)
            d22 = (Vp)/(self.time_step*fvfo)*-1

            self.D = diags(-d22/d12*d11+d21)

            Uxm = self.pressure[:,index][cxm_0]>self.pressure[:,index][cxm_m]
            Uxp = self.pressure[:,index][cxp_0]>self.pressure[:,index][cxp_p]
            Uym = self.pressure[:,index][cym_0]>self.pressure[:,index][cym_m]
            Uyp = self.pressure[:,index][cyp_0]>self.pressure[:,index][cyp_p]
            Uzm = self.pressure[:,index][czm_0]>self.pressure[:,index][czm_m]
            Uzp = self.pressure[:,index][czp_0]>self.pressure[:,index][czp_p]

            krw,kro = self.rp.water_oil(Sw=self.Sw[:,index])

            krw_xm[Uxm] = krw[cxm_0][Uxm]
            krw_xp[Uxp] = krw[cxp_0][Uxp]
            krw_ym[Uym] = krw[cym_0][Uym]
            krw_yp[Uyp] = krw[cyp_0][Uyp]
            krw_zm[Uzm] = krw[czm_0][Uzm]
            krw_zp[Uzp] = krw[czp_0][Uzp]

            krw_xm[~Uxm] = krw[cxm_m][~Uxm]
            krw_xp[~Uxp] = krw[cxp_p][~Uxp]
            krw_ym[~Uym] = krw[cym_m][~Uym]
            krw_yp[~Uyp] = krw[cyp_p][~Uyp]
            krw_zm[~Uzm] = krw[czm_m][~Uzm]
            krw_zp[~Uzp] = krw[czp_p][~Uzp]

            kro_xm[Uxm] = kro[cxm_0][Uxm]
            kro_xp[Uxp] = kro[cxp_0][Uxp]
            kro_ym[Uym] = kro[cym_0][Uym]
            kro_yp[Uyp] = kro[cyp_0][Uyp]
            kro_zm[Uzm] = kro[czm_0][Uzm]
            kro_zp[Uzp] = kro[czp_0][Uzp]

            kro_xm[~Uxm] = kro[cxm_m][~Uxm]
            kro_xp[~Uxp] = kro[cxp_p][~Uxp]
            kro_ym[~Uym] = kro[cym_m][~Uym]
            kro_yp[~Uyp] = kro[cyp_p][~Uyp]
            kro_zm[~Uzm] = kro[czm_m][~Uzm]
            kro_zp[~Uzp] = kro[czp_p][~Uzp]

            TXMw = (self.TXM[self.res.grid_hasxmin]*krw_xm)/(muw*fvfw)*6.33e-3 # unit conversion
            TYMw = (self.TYM[self.res.grid_hasymin]*krw_ym)/(muw*fvfw)*6.33e-3 # unit conversion
            TZMw = (self.TZM[self.res.grid_haszmin]*krw_zm)/(muw*fvfw)*6.33e-3 # unit conversion

            TXPw = (self.TXP[self.res.grid_hasxmax]*krw_xp)/(muw*fvfw)*6.33e-3 # unit conversion
            TYPw = (self.TYP[self.res.grid_hasymax]*krw_yp)/(muw*fvfw)*6.33e-3 # unit conversion
            TZPw = (self.TZP[self.res.grid_haszmax]*krw_zp)/(muw*fvfw)*6.33e-3 # unit conversion

            TXMn = (self.TXM[self.res.grid_hasxmin]*kro_xm)/(muo*fvfo)*6.33e-3 # unit conversion
            TYMn = (self.TYM[self.res.grid_hasymin]*kro_ym)/(muo*fvfo)*6.33e-3 # unit conversion
            TZMn = (self.TZM[self.res.grid_haszmin]*kro_zm)/(muo*fvfo)*6.33e-3 # unit conversion

            TXPn = (self.TXP[self.res.grid_hasxmax]*kro_xp)/(muo*fvfo)*6.33e-3 # unit conversion
            TYPn = (self.TYP[self.res.grid_hasymax]*kro_yp)/(muo*fvfo)*6.33e-3 # unit conversion
            TZPn = (self.TZP[self.res.grid_haszmax]*kro_zp)/(muo*fvfo)*6.33e-3 # unit conversion

            self.Tw = csr(mshape)

            self.Tw -= csr((TXMw,(cxm_0,cxm_m)),shape=mshape)
            self.Tw += csr((TXMw,(cxm_0,cxm_0)),shape=mshape)

            self.Tw -= csr((TXPw,(cxp_0,cxp_p)),shape=mshape)
            self.Tw += csr((TXPw,(cxp_0,cxp_0)),shape=mshape)

            self.Tw -= csr((TYMw,(cym_0,cym_m)),shape=mshape)
            self.Tw += csr((TYMw,(cym_0,cym_0)),shape=mshape)

            self.Tw -= csr((TYPw,(cyp_0,cyp_p)),shape=mshape)
            self.Tw += csr((TYPw,(cyp_0,cyp_0)),shape=mshape)

            self.Tw -= csr((TZMw,(czm_0,czm_m)),shape=mshape)
            self.Tw += csr((TZMw,(czm_0,czm_0)),shape=mshape)

            self.Tw -= csr((TZPw,(czp_0,czp_p)),shape=mshape)
            self.Tw += csr((TZPw,(czp_0,czp_0)),shape=mshape)

            self.Tn = csr(mshape)

            self.Tn -= csr((TXMn,(cxm_0,cxm_m)),shape=mshape)
            self.Tn += csr((TXMn,(cxm_0,cxm_0)),shape=mshape)

            self.Tn -= csr((TXPn,(cxp_0,cxp_p)),shape=mshape)
            self.Tn += csr((TXPn,(cxp_0,cxp_0)),shape=mshape)

            self.Tn -= csr((TYMn,(cym_0,cym_m)),shape=mshape)
            self.Tn += csr((TYMn,(cym_0,cym_0)),shape=mshape)

            self.Tn -= csr((TYPn,(cyp_0,cyp_p)),shape=mshape)
            self.Tn += csr((TYPn,(cyp_0,cyp_0)),shape=mshape)

            self.Tn -= csr((TZMn,(czm_0,czm_m)),shape=mshape)
            self.Tn += csr((TZMn,(czm_0,czm_0)),shape=mshape)

            self.Tn -= csr((TZPn,(czp_0,czp_p)),shape=mshape)
            self.Tn += csr((TZPn,(czp_0,czp_0)),shape=mshape)

            self.T = diags(-d22/d12)*self.Tw+self.Tn

            krw,kro = self.rp.water_oil(Sw=self.Sw[:,index][self.well_grids])

            Jw_v = (self.JR*krw)/(muw*fvfw)*6.33e-3 # unit conversion
            Jn_v = (self.JR*kro)/(muo*fvfo)*6.33e-3 # unit conversion

            self.Jw = csr((Jw_v[cpw],(self.well_grids[cpw],self.well_grids[cpw])),shape=mshape)
            self.Jn = csr((Jn_v[cpo],(self.well_grids[cpo],self.well_grids[cpo])),shape=mshape)

            self.J = diags(-d22/d12)*self.Jw+self.Jn
            
            self.Qw = csr(vshape)
            self.Qn = csr(vshape)

            qw_cp = self.well_limits[cpw]*Jw_v[cpw]
            qo_cp = self.well_limits[cpo]*Jn_v[cpo]

            qw_cr = self.well_limits[cqw]*(krw[cqw]*muo)/(krw[cqw]*muo+kro[cqw]*muw)
            qo_cr = self.well_limits[cqo]*(kro[cqo]*muw)/(krw[cqo]*muo+kro[cqo]*muw)

            qw_cr[sp_wf[cqw]] = self.well_limits[sp_wf]
            qo_cr[sp_of[cqo]] = self.well_limits[sp_of]

            self.Qw += csr((qw_cp,(self.well_grids[cpw],vzeros[cpw])),shape=vshape)
            self.Qn += csr((qo_cp,(self.well_grids[cpo],vzeros[cpo])),shape=vshape)

            self.Qw += csr((qw_cr*5.61,(self.well_grids[cqw],vzeros[cqw])),shape=vshape) # unit conversion
            self.Qn += csr((qo_cr*5.61,(self.well_grids[cqo],vzeros[cqo])),shape=vshape) # unit conversion

            self.Qw = self.Qw.toarray().flatten()
            self.Qn = self.Qn.toarray().flatten()

            self.Q = -d22/d12*self.Qw+self.Qn

            self.pressure[:,index+1] = sps(self.T+self.J+self.D,self.D.dot(self.pressure[:,index])+self.Q)

            delta_p = (self.pressure[:,index+1]-self.pressure[:,index])
            
            tjp = csr.dot(self.Tw+self.Jw,self.pressure[:,index+1])

            self.Sw[:,index+1] = self.Sw[:,index]-(d11*delta_p-self.Qw+tjp)/d12

        for index,(p,sw) in enumerate(zip(self.pressure[:,-1],self.Sw[:,-1])):
            print("{:d}\tP\t{:4.1f}\tSw\t{:.5f}".format(index,p,sw))

class TwoPhaseSS():
    
    def __init__(self):

        pass

    def set_time(self,step,total):

        self.timesteps = np.arange(0,total+step,step)

    def solve():

        pass

if __name__ == "__main__":

    import unittest

    from tests import test_porous_media

    unittest.main(test_porous_media)