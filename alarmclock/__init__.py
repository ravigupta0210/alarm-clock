"""A small, dependency-free CLI alarm clock.

The package separates pure logic (`parsing`) from side-effecting I/O
(`sound`, `scheduler`) so the tricky time math can be unit-tested without
real clocks or real sleeping.
"""

__version__ = "1.0.0"
