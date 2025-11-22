"""フィッティングエンジン - 各種近似手法の実装"""

from app.core.fitting.exp import ExponentialFitter
from app.core.fitting.log import LogarithmicFitter
from app.core.fitting.ludwik import LudwikFitter
from app.core.fitting.poly import PolynomialFitter
from app.core.fitting.power import PowerFitter
from app.core.fitting.registry import FitterRegistry
from app.core.fitting.swift import SwiftFitter
from app.core.fitting.voce import VoceFitter

# 全フィッターをRegistryに自動登録
FitterRegistry.register("ludwik", LudwikFitter)
FitterRegistry.register("swift", SwiftFitter)
FitterRegistry.register("voce", VoceFitter)
FitterRegistry.register("poly", PolynomialFitter)
FitterRegistry.register("exp", ExponentialFitter)
FitterRegistry.register("log", LogarithmicFitter)
FitterRegistry.register("power", PowerFitter)

__all__ = [
    "FitterRegistry",
    "LudwikFitter",
    "SwiftFitter",
    "VoceFitter",
    "PolynomialFitter",
    "ExponentialFitter",
    "LogarithmicFitter",
    "PowerFitter",
]
