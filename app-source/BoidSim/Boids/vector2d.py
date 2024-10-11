"""Simple 2D vectors."""
import math
import cmath

@micropython.native
class Vector2D:
    """A 2D vector class."""

    def __init__(self, x: complex, y: float = 0):
        """Construct the Vector2D.

        Args can be either x/y floats, or a complex number.
        """
        self.z = complex(x, y)
        self.x = self.z.real
        self.y = self.z.imag

    @staticmethod
    def mean(vectors: list['Vector2D']) -> 'Vector2D':
        """Return the mean (average) of all vectors in the list."""
        x = 0.0
        y = 0.0
        count = 0
        for vec in vectors:
            x += vec.x
            y += vec.y
            count += 1
        return Vector2D(x/count, y/count)

    # ~~~~~~~~~~~~ __dunders__: ~~~~~~~~~~~~

    @staticmethod
    def __len__() -> int:
        return 2

    def __complex__(self) -> complex:
        return self.z

    def __eq__(self, other: 'Vector2D') -> bool:
        return bool(
            isinstance(other, Vector2D)
            and other.x == self.x
            and other.y == self.y
        )

    def __add__(self, other: 'Vector2D'|float) -> 'Vector2D':
        if isinstance(other, Vector2D):
            return Vector2D(self.x+other.x, self.y+other.y)
        return Vector2D(self.x+other, self.y+other)

    def __sub__(self, other: 'Vector2D'|float) -> 'Vector2D':
        if isinstance(other, Vector2D):
            return Vector2D(self.x-other.x, self.y-other.y)
        return Vector2D(self.x-other, self.y-other)

    def __rsub__(self, other: float) -> 'Vector2D':
        return Vector2D(other-self.x, other-self.y)

    def __mul__(self, other: 'Vector2D'|float) -> 'Vector2D':
        if isinstance(other, Vector2D):
            return Vector2D(self.x*other.x, self.y*other.y)
        return Vector2D(self.x*other, self.y*other)

    def __matmul__(self, other: 'Vector2D'|float) -> 'Vector2D':
        if isinstance(other, Vector2D):
            other = complex(other)
        return Vector2D(complex(self) * other)

    def __truediv__(self, other: 'Vector2D'|float) -> 'Vector2D':
        if isinstance(other, Vector2D):
            return Vector2D(self.x/other.x, self.y/other.y)
        return Vector2D(self.x/other, self.y/other)

    def __floordiv__(self, other: 'Vector2D'|float) -> 'Vector2D':
        if isinstance(other, Vector2D):
            return Vector2D(self.x//other.x, self.y//other.y)
        return Vector2D(self.x//other, self.y//other)

    def __mod__(self, other: 'Vector2D'|float) -> 'Vector2D':
        if isinstance(other, Vector2D):
            return Vector2D(self.x%other.x, self.y%other.y)
        return Vector2D(self.x%other, self.y%other)

    def __pow__(self, other: 'Vector2D'|float) -> 'Vector2D':
        if isinstance(other, Vector2D):
            return Vector2D(self.x**other.x, self.y**other.y)
        return Vector2D(self.x**other, self.y**other)

    def __abs__(self) -> 'Vector2D':
        return Vector2D(abs(self.x), abs(self.y))

    def __repr__(self) -> str:
        return f"Vector2D({self.x}, {self.y})"

    # ~~~~~~~~~~~~ other_math: ~~~~~~~~~~~~
    def isclose(self, other: 'Vector2D', rel_tol=0.00001) -> bool:
        """Check if vector is roughly equal to another vector."""
        return (
            math.isclose(self.x, other.x, rel_tol=rel_tol)
            and math.isclose(self.y, other.y, rel_tol=rel_tol)
        )

    def rotate(self, degrees) -> 'Vector2D':
        """Rotate vector around 0,0 by given degrees."""
        return complex(self) * 1j**(degrees/90)

    def magnitude(self) -> float:
        """Get the magnitude of the vector."""
        return abs(complex(self))
    def phase(self) -> float:
        """Get the phase of the vector."""
        return cmath.phase(self.z)

    def flipped(self) -> 'Vector2D':
        """Return a flipped copy of this vector."""
        return Vector2D(-complex(self))

    def distance(self, other: 'Vector2D') -> float:
        """Get the distance between this, and another vector."""
        return abs(complex(self) - complex(other))

    def polar(self) -> 'Vector2D':
        """Convert from rectangular to polar coordinates."""
        return Vector2D(*cmath.polar(self.z))

    def rect(self) -> 'Vector2D':
        """Convert from polar to rectangular coordinates."""
        return Vector2D(cmath.rect(self.x, self.y))

# Avoid redefining methods that work the same in reverse:
Vector2D.__radd__ = Vector2D.__add__
Vector2D.__rmul__ = Vector2D.__mul__
