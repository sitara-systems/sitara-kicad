"""sitara_av - generate and verify AV signal-flow drawings in KiCad 10 with the Sitara symbol libraries.

    from sitara_av import Context, Sheet, SYMBOLS, gr, palette
    from sitara_av.build import BuildConfig, build
"""
from . import checks, palette, theme  # noqa: F401
from .sheet import Context, Inst, Sheet, SYMBOLS, T, gr  # noqa: F401
