#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 23 12:01:21 2022

@author: bennett
"""
import math
import scipy.integrate as integrate 
from .benchmark_functions import uncollided_square_source, uncollided_square_IC, gaussian_source_integrand, uncollided_gauss_2D_integrand
import numpy as np

def opts0(*args, **kwargs):
       return {'limit':10000000}
def opts1(*args, **kwargs):
       return {'limit':100 }
   
###############################################################################

class uncollided_class:
    
    def __init__(self, source_type, x0, t0, sigma):
        self.source_type = source_type
        self.x0 = x0
        self.t0 = t0
        self.sigma = sigma
        
       
    def plane_IC(self, xs, t):
        """ uncollided scalar flux for 1D plane pulse 
        """
        temp = xs*0
        for ix in range(xs.size):
            if (-t <= xs[ix] <= t):
                temp[ix] = math.exp(-t)/(2*t+1e-12)
        return temp
        
    def square_IC(self, xs, t):
        """ uncollided scalar flux for 1D square pulse 
        """
        temp = xs*0
        for ix in range(xs.size):
            x = xs[ix]
            temp[ix] = uncollided_square_IC(x, t, self.x0)
        return temp
    
    def square_source(self, xs, t):
        """ uncollided scalar flux for 1D square source
        """
        temp = xs*0
        for ix in range(xs.size):
            x = xs[ix]
            temp[ix] = uncollided_square_source(x, t, self.x0, self.t0)
        return temp
    def gaussian_IC(self, xs, t):
        """ uncollided scalar flux for 1D Gaussian pulse with standard deviation x0
        """
        temp = xs*0
        sqrtpi = math.sqrt(math.pi)
        for ix in range(xs.size):
            xx = xs[ix]
            temp[ix] = math.exp(-t) * sqrtpi * self.sigma * (math.erf((t-xx)/self.sigma) + math.erf((t+xx)/self.sigma))/(4.0 * t + 1e-14)  
        return temp 
    
    def gaussian_source(self, xs, t):
        """ uncollided scalar flux for 1D Gaussian source with standard deviation x0
        """
        self.t0 = min(self.t0, t)
        temp = xs*0
        sqrtpi = math.sqrt(math.pi)
        for ix in range(xs.size):
            x = xs[ix]
            result = integrate.nquad(gaussian_source_integrand, [[0, self.t0]], args =  (t, x, self.sigma))[0]
            temp[ix] = result
        return temp * sqrtpi * self.sigma  
    
    def uncollided_gauss_2D_first_integral(self, v, x, y, t):
        """ integrates the line source over s (x dummy variable)
        """
        sqrt_term = t**2 - v**2 + 2*v*y - y**2
        res = 0.0
        if sqrt_term >= 0:
            a = x - math.sqrt(sqrt_term)
            b = x + math.sqrt(sqrt_term)
            
            res = integrate.nquad(uncollided_gauss_2D_integrand, [[a, b]], args = (v, x, y, t), opts = [opts1])[0]
        return res

    def uncollided_gauss_2D_second_integral(self, x, y, t):
        """ integrates the line source over v (y dummy variable)
        """
        res = integrate.nquad(self.uncollided_gauss_2D_first_integral, [[-np.inf, np.inf]], args = (x, y, t), opts = [opts1])[0]
        return res
    
    def gaussian_IC_2D(self, rhos, t):
        temp = rhos*0
        for ix in range(rhos.size):
            rho = rhos[ix]
            temp[ix] = self.uncollided_gauss_2D_second_integral(rho, 0, t)
        return temp
    
    def line_source(self, rhos, t):
        temp = rhos*0
        for ix in range(rhos.size):
            rho = rhos[ix]
            temp[ix] = uncollided_gauss_2D_integrand(0, 0, rho, 0, t)
        return temp
    
    def point_source(self, rhos, t):   
        temp = rhos*0
        for ix in range(rhos.size):
            rho = rhos[ix]
            if abs(rho-t) <= 1e-10:
                temp[ix] = math.exp(-t)/4/math.pi/t**2/rho
        return temp*0
    
    def shell_source(self, xs, t):
        # R = self.x0
        # # a = self.x0/2
        # q0 = 4 * math.pi * R**3 / 3
        # temp = rhos *0
        # for ix in range(rhos.size):
        #     r = rhos[ix]
        #     integrand = lambda omega: omega * (self.plane_IC(np.array([np.abs(R*omega-r)]), t) - self.plane_IC(np.array([np.abs(R*omega+r)]), t)) 
        #     res = integrate.nquad(integrand, [[0, 1]], opts = [opts0])[0]
        #     temp[ix] = res * 3 / 4 /math.pi /R / (r + 1e-16)
        temp = xs*0 
        x0 = self.x0
        sigma_abs = 1.0
        N01  = 4 * math.pi * x0**3 / 3
        N0 = 1
        n0 = N0 / (4. * math.pi / 3. * (x0 ** 3)) / (4. * math.pi)
        for ix, r in enumerate(xs):
            if t >0:
                tt = t 
                mu_crit = min(1., max(-1.,0.5*(tt/r+r/tt-x0**2/(r*tt))))
                r2 = r ** 2 + t ** 2 - 2 * mu_crit * r * t
                # if np.sqrt(r2) < self.x0: 
                temp[ix] = n0 * 2 * math.pi *  (1. - mu_crit ) * np.exp(-t * sigma_abs) 
            elif t == 0:
                temp[xs <= self.x0] = n0 * 4 * math.pi
        return temp



    
    def __call__(self, xs, t):
        if self.source_type == 'plane_IC':
            return self.plane_IC(xs, t)
        elif self.source_type == 'square_IC':
            return self.square_IC(xs, t)
        elif self.source_type == 'square_source':
            return self.square_source(xs, t)
        elif self.source_type == 'gaussian_IC':                
            return self.gaussian_IC(xs, t)
        elif self.source_type == 'gaussian_source':
            return self.gaussian_source(xs, t)
        elif self.source_type == 'gaussian_IC_2D':
            return self.gaussian_IC_2D(xs, t)
        elif self.source_type == "line_source":
            return self.line_source(xs, t)
        elif self.source_type == 'point_source':
            return self.point_source(xs, t)
        elif self.source_type == 'shell_source':
            return self.shell_source(xs, t)
        
        
        
        
        
        
        