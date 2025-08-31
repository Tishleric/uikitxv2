# Python 3.11, Jupyter-ready
import math
from typing import Callable, Tuple

SQRT2 = math.sqrt(2.0); SQRT2PI = math.sqrt(2.0*math.pi)
def norm_pdf(x): return math.exp(-0.5*x*x)/SQRT2PI
def norm_cdf(x): return 0.5*math.erfc(-x/SQRT2)

def bachelier_call(S: float, K: float, sigma_n: float, T: float) -> float:
    if sigma_n <= 0: return max(S-K, 0.0)
    rt = math.sqrt(T); d = (S-K)/(sigma_n*rt)
    return (S-K)*norm_cdf(d) + sigma_n*rt*norm_pdf(d)

def bachelier_put(S: float, K: float, sigma_n: float, T: float) -> float:
    if sigma_n <= 0: return max(K-S, 0.0)
    rt = math.sqrt(T); d = (K-S)/(sigma_n*rt)
    return (K-S)*norm_cdf(d) + sigma_n*rt*norm_pdf(d)

def black_scholes_call(S: float, K: float, sigma_n: float, T: float) -> float:
    if sigma_n <= 0: return max(S-K, 0.0)
    d1 = (math.log(S/K) + (0.5*sigma_n**2)*T)/(sigma_n*math.sqrt(T))
    d2 = d1 - sigma_n*math.sqrt(T)
    return S*norm_cdf(d1) - K*norm_cdf(d2)

class Counter:
    def __init__(self, f: Callable[[float], float]): self.f, self.n = f, 0
    def __call__(self, x): self.n += 1; return self.f(x)

def brentq(f: Callable[[float], float], a: float, b: float,
           xtol: float=1e-12, ftol: float=1e-12, maxit: int=200) -> Tuple[float,int]:
    fa, fb = f(a), f(b)
    if not (fa<=0<=fb or fb<=0<=fa): raise ValueError("Need a sign-change bracket.")
    if fa == 0: return a, 1
    if fb == 0: return b, 2
    c, fc = a, fa; d = e = b-a; it = 0
    while it < maxit:
        it += 1
        if abs(fc) < abs(fb): a,b,c = b,c,b; fa,fb,fc = fb,fc,fb
        tol = 2.0*xtol*max(1.0, abs(b)); m = 0.5*(c-b)
        if abs(m) <= tol or abs(fb) <= ftol: return b, it
        if abs(e) >= tol and abs(fa) > abs(fb):
            s = fb/fa
            if a != c and fa != fc:
                q = fa/fc; r = fb/fc
                p = s*(2.0*m*q*(q-r) - (b-a)*(r-1.0)); q = (q-1.0)*(r-1.0)*(s-1.0)
            else:
                p = s*(b-a); q = 1.0 - s
            if p > 0: q = -q
            p = abs(p)
            if 2.0*p < min(3.0*abs(m)*abs(q) - abs(tol*q), abs(e*q)):
                e, d = d, p/q
            else:
                d = m; e = m
        else:
            d = m; e = m
        a, fa = b, fb
        b = b + (d if abs(d) > tol else (tol if m > 0 else -tol))
        fb = f(b)
        if (fb > 0 and fc > 0) or (fb < 0 and fc < 0):
            c, fc = a, fa; e = d = b - a
    return b, it

def bisection(f: Callable[[float], float], a: float, b: float,
              xtol: float=1e-16, ftol: float=1e-12, maxit: int=400) -> Tuple[float,int]:
    fa, fb = f(a), f(b)
    if fa == 0: return a, 1
    if fb == 0: return b, 2
    if fa*fb > 0: raise ValueError("Need a sign-change bracket.")
    it = 0
    while it < maxit:
        it += 1
        c = 0.5*(a+b); fc = f(c)
        if abs(fc) <= ftol or abs(b-a) <= xtol*(1+abs(c)): return c, it
        if fa*fc < 0: b, fb = c, fc
        else: a, fa = c, fc
    return 0.5*(a+b), it


def implied_vol(S,K,T,C):

    def f_sigma(sig): return bachelier_call(S, K, sig, T) - C

    # Bracket [0, hi] by geometric expansion
    lo, hi = 0.0, 1e-4
    while f_sigma(hi) < 0: hi *= 2.0

    f2 = Counter(f_sigma); root_bis, it_bis = bisection(f2, lo, hi, xtol=1e-16, ftol=1e-16)

    return root_bis

if __name__ == "__main__":
    # Deep OTM example (tweak to your market): price tiny, monotone in sigma
    S, K, T = 111.75, 110.0, 0.003538
    C_mkt = 1.75
    # Root function in sigma: f(sig) = model - market
    def f_sigma(sig): return bachelier_call(S, K, sig, T) - C_mkt

    # Bracket [0, hi] by geometric expansion
    lo, hi = 0.0, 1e-4
    while f_sigma(hi) < 0: hi *= 2.0

    f1 = Counter(f_sigma); root_b, it_b = brentq(f1, lo, hi, xtol=1e-16, ftol=1e-16)
    f2 = Counter(f_sigma); root_bis, it_bis = bisection(f2, lo, hi, xtol=1e-16, ftol=1e-16)

    print("Recalculated Price_brentq", bachelier_call(S,K, root_b, T))
    print("Recalculated Price_bisect", bachelier_call(S,K, root_bis, T))

    print(f"Brent:    sigma={root_b:.12g}, iters={it_b}, f-evals={f1.n}")
    print(f"Bisection:sigma={root_bis:.12g}, iters={it_bis}, f-evals={f2.n}")

    F = 112
    
