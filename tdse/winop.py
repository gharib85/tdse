import numpy as np

from .integral import eval_norm_trapezoid
from .evol import get_D2_tridiag, get_M2_tridiag, mul_tridiag_and_diag
from .matrix_py import tridiag_forward, tridiag_backward


def eval_energy_spectrum_for_1D_hamil(
        sf_arr, x_arr, V_x_arr, E_arr, winop_n, gamma):
    
    ## Define some variables
    _N_x = x_arr.size
    _delta_x = x_arr[1] - x_arr[0]
    
    ## Allocate memory
    # for output
    spectrum_E_arr = np.empty_like(E_arr, dtype=float)
    # for intermediate result
    right_arr = np.empty_like(x_arr, dtype=complex)
    root_W_sf_arr = np.empty_like(x_arr, dtype=complex)

    ## Evaluate constant components
    D2 = get_D2_tridiag(_N_x, _delta_x)
    M2 = get_M2_tridiag(_N_x)
    M2V = mul_tridiag_and_diag(M2, V_x_arr)

    norm_const = np.sin(np.pi/2**winop_n) / (np.pi/2**winop_n)
    tridiag_forward(gamma*M2, sf_arr, right_arr)
    winop_left_tridiag_static = -0.5*D2 + M2V + (1.0j*gamma)*M2

    ## Evaluate energy-dependent values
    for E_idx, E0 in enumerate(E_arr):
        winop_left_tridiag = winop_left_tridiag_static - E0 * M2
        tridiag_backward(winop_left_tridiag, root_W_sf_arr, right_arr)
        spectrum_E_arr[E_idx] = 1.0 / (2.0*gamma) * norm_const * eval_norm_trapezoid(x_arr, root_W_sf_arr)
        
    return spectrum_E_arr

