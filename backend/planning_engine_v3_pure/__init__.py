"""
V3 PURE - Timeline Linéaire (NO V2 LOGIC ALLOWED)

Backend engine for V3 planning with linear timeline architecture.

Key concepts:
- Time: Relative minutes from planningStartTime (minuteOffset: int)
- Algorithm: 2-step (ORDERING → TIME CALCULATION)
- No imports from backend.planning_engine (old code)
- Uses TaskV3, Obstacle, Timeline types
"""

__version__ = "3.0.0-pure"
__architecture__ = "linear-timeline"
