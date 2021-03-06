"""Base propagator object"""

import numpy as np
from numpy import pi, sqrt

class Wavefunction(object):
    """Base class for wavefunction objects"""
    
    @staticmethod
    def norm_sq(wf, *args):
        """Evaluate norm square of the given wavefunction"""
        pass

    @classmethod
    def normalize(cls, wf, *args):
        """Normalize the given wavefunction inplace"""
        _norm_sq = cls.norm_sq(wf, *args)
        wf *= 1. / sqrt(_norm_sq)



class Propagator(object):
    
    wf_class = Wavefunction

    def propagate(self, *args, **kwargs):
        pass

    def propagate_to_ground_state(self, wf, dt, max_Nt, normalizer_args,
                                  Nt_per_iter=10, norm_thres=1e-13, 
                                  wfs_to_substract=()):
        """
        Propagate the given wavefunction by the imaginary timestep
        to get the lowest energy possible from the given initial wavefunction
        """

        # Determine timestep
        _dt = float(dt)
        if not (_dt > 0): 
            _msg = "`dt` should be a positive real number. Given: {}"
            raise ValueError(_msg.format(_dt))
        _imag_dt = -1.0j * _dt # imaginary time for propagating to ground state
        
        # Check `wfs_to-substract`
        assert type(wfs_to_substract) in (list, tuple, np.ndarray)

        # Initialize
        self.wf_class.normalize(wf, *normalizer_args)
        _wf_prev = wf.copy()
        
        # Propagate the wavefunction by the imaginary timestep
        # to get the lowest energy possible from the given initial wavefunction
        _max_iter = int(max_Nt / Nt_per_iter) + 1
        for _i in range(_max_iter):
            self.propagate(wf, _imag_dt, Nt=Nt_per_iter)

            # Let our wavefunction to be orthogonal to given wavefunction(s)
            for _wf_sub in wfs_to_substract:
                wf -= _wf_sub * self.wf_class.inner(wf, _wf_sub, self.dx)

            self.wf_class.normalize(wf, *normalizer_args)
            _norm = self.wf_class.norm_sq(wf - _wf_prev, *normalizer_args)
            if not (_i % 100):
                print("[_i={:05d}] _norm = {:.16e}".format(_i, _norm))
            if _norm < norm_thres: break
            _wf_prev = wf.copy()
        if _i >= _max_iter-1: raise Exception("Maximum iteration exceeded")
        else: print("iteration count at end: {}".format(_i*Nt_per_iter))



def _eval_f_and_derivs_by_FD(_r, _Rm, _dr, _r0=0.0, _with_fd_rlim=False):
    """
    Evaluate values of a function and its derivatives
    from the function values on a regular (i.e. uniform) one dimensional grid
    
    Parameters
    ----------
    Rm : (Nm, Nr) or (Nr,) array-like
        
    """
    _Nr = _Rm.shape[-1]
    _rmin, _rmax = _r0, _r0 + (_Nr - 1) * _dr
    assert _rmin <= _r and _r < _rmax

    _Ns = 4
    _il = int((_r - _rmin) // _dr)
    _is0 = (_il-1) \
            + (_il < 1) * (1 - _il) \
            + (_il > _Nr-3) * (_Nr-3 - _il)
#    _r_arr = np.arange(_Nr) * _dr
    _r_arr_slice = _rmin + np.arange(_is0,_is0+_Ns) * _dr
#    _rn_minus_r = _r_arr[_is0:_is0+_Ns] - _r
    _rn_minus_r = _r_arr_slice - _r
    _A = np.empty((_Ns, _Ns), dtype=float)
    _A[:,0] = 1.0
    for _is in range(1,_Ns):
        _A[:,_is] = _A[:,_is-1] * _rn_minus_r / _is
    _b = _Rm[...,_is0:_is0+_Ns].transpose()  # b.ndim may be 1 or 2
   
    try: _Rm_derivs = np.linalg.solve(_A, _b)
    except np.linalg.LinAlgError as e:
        raise RuntimeError("Failed to get Rm deriv for r{}".format(_r))
    except: raise Exception("Unexpected error")

    _result = _Rm_derivs
    if _with_fd_rlim: _result = (_Rm_derivs, _r_arr_slice[[0,-1]])
    return _result


