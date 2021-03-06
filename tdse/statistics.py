"""routine for several statistics"""

import numpy as np

class ReducedSupport(list):
    def __init__(self, x_arr, start_indices, lengths):
        
        assert isinstance(x_arr, np.ndarray)
        
        self.x_arr = x_arr
        self.start_indices = start_indices
        self.lengths = lengths
        _iterable = (x_arr[i:i+l] for i, l in zip(start_indices, lengths))

        super().__init__(_iterable)

        self.index_exp_list = [
            np.index_exp[i:i+l] 
            for i, l in zip(self.start_indices, self.lengths)]
    
    @classmethod
    def from_distribution_and_threshold(_class, x_arr, fx_arr, fx_threshold):
        assert isinstance(fx_arr, np.ndarray) and not np.any(fx_arr < 0)
        _rsup_mask = fx_arr > fx_threshold
        _start_indices, _lengths = _class.extract_start_indices_and_lengths_of_true_segment(_rsup_mask)
        return _class(x_arr, _start_indices, _lengths)
       
    @staticmethod
    def extract_start_indices_and_lengths_of_true_segment(arr):
        _kernel = np.array((1,-1))
        _indicator = np.convolve(arr, _kernel, mode='full')
        _indices_true_after_false, = np.where(_indicator > 0)
        _indices_false_after_true, = np.where(_indicator < 0)
        
        _start_indices_of_true_segment = _indices_true_after_false
        _lengths = _indices_false_after_true - _indices_true_after_false
        return _start_indices_of_true_segment, _lengths
    
    def integrate_distribution(self, fx_arr):
        assert isinstance(fx_arr, np.ndarray)
        assert (fx_arr.ndim == 1) and (fx_arr.size == self.x_arr.size)
        _sum = 0.0
        for i, l in zip(self.start_indices, self.lengths):
            _slice = slice(i,i+l)
            _sum += np.trapz(fx_arr[_slice], x=self.x_arr[_slice])
        return _sum



from scipy.optimize import brentq

def eval_prob_density_threshold(x_arr, fx_arr, norm_to_match, norm_tol):
    """Evaluates a threshold of the given probability density"""

    def _ff(_fx_thres, _x_arr, _fx_arr, _norm_to_match):
        _fx_rsup = np.ma.array(_fx_arr, copy=False, mask=~(_fx_arr > _fx_thres))
        _norm = np.ma.sum(_fx_rsup[:-1] * np.diff(_x_arr))
        if isinstance(_norm, np.ma.core.MaskedConstant):
            if np.all(_fx_rsup.mask):
                _norm = 0.0
            else: raise Exception(
                    "Unexpected during norm evaluation of an masked array")
        return _norm - _norm_to_match

    _fargs = (x_arr, fx_arr, norm_to_match)
    _x0, _root_info = brentq(_ff, a=0.0, b=fx_arr.max(), 
                             args=_fargs, full_output=True)
    
    if not _root_info.converged:
        raise Exception("Failed to find the threshold")
    
    _norm_deviation = _ff(_x0, x_arr, fx_arr, norm_to_match)
    _out_of_norm_tol = abs(_norm_deviation) >= norm_tol
    if _out_of_norm_tol:
        print("root info:\n{}".format(_root_info))
        raise Exception("The norm is out of norm tolerance.\n" \
                + "The norm at the converged threshold (={}): {}".format(
                    _x0, norm_to_match + _norm_deviation))
    
    return _x0




from .integral import integrate_on_reg_grid

def norm_above_thres(thres, fx, *dxargs):
    _ma = np.ma.array(fx, mask=fx<=thres)
    _norm = integrate_on_reg_grid(_ma, *dxargs)
    return _norm


from scipy.optimize import brentq

def thres_to_get_given_norm(norm, norm_tol, fx, *dxargs):
    
    if not (len(dxargs) > 0):
        raise ValueError("No grid spacing (`dxargs`) given")

    def _f(_thres, _norm, _fx, *_dxargs):
        _norm = norm_above_thres(_thres, _fx, *_dxargs)
        return _norm - norm
    _fargs = (norm, fx,) + dxargs

    _thres0, _res = brentq(_f, a=0.0, b=fx.max(), args=_fargs, full_output=True)
    if not _res.converged:
        raise Exception("The solution not converged")

    _norm_deviation = _f(_thres0, *_fargs)
    if abs(_norm_deviation) >= norm_tol:
        _mesg_form = "The norm(={}) at found threshold " \
            + "is out of norm tolerence range({} <= norm <= {}).\n" \
            + "Consider rasing `norm_tol` to enlarge the tolerence range"
        _mesg = _mesg_form.format(
                norm+_norm_deviation,norm-norm_tol,norm+norm_tol)
        raise Exception(_mesg)

    return _thres0



def mean_and_std_from_prob_density(pdf, x, mean_only=True):
    """
    Evaluate mean and standard deviation of given probability density function
    
    Caution
    ----------
    Do not use for masked array since this routine utilizes `numpy.trapz` 
    which may result some losses when dealing with the masked array
    
    Argument
    ----------
    pdf : array-like (...,N)
        probability density function
    x : array-like (,N)
        array of random variable
        should be monotonically increasing
        i.e. `x[i] <= x[i+1] for i=0,1,...,N-2`
    """
    _pdf, _x = np.array(pdf, copy=False), np.array(x, copy=False)
    assert _x.ndim == 1 and _pdf.ndim >= 1 and _pdf.shape[-1] == _x.size
    
    _x_n_pdf = _x*_pdf
    _E_X = np.trapz(_x_n_pdf, _x, axis=-1)
    _mean = _E_X
    if mean_only: return _mean
    
    _x_n_pdf *= _x
    _E_X2 = np.trapz(_x_n_pdf, _x, axis=-1)
    _var = _E_X2 - _E_X*_E_X
    _std = np.sqrt(_var)
    return _mean, _std
