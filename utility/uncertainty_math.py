import math
import numpy as np


def add(x, dx, y, dy):
    """
    Calculate the sum; z = x + y, with error/uncertainty propagation.
    """
    z = np.add(x, y)
    dz = uncertainty_add_or_subtract(dx, dy)
    return z, dz


def subtract(x, dx, y, dy):
    """
    Calculate the sum; z = x + y, with error/uncertainty propagation.
    """
    z = np.subtract(x, y)
    dz = uncertainty_add_or_subtract(dx, dy)
    return z, dz


def multiply(x, dx, y, dy):
    """
    Calculate the product; z = x * y, with error/uncertainty propagation.
    """
    z = np.multiply(x, y)
    dz = uncertainty_multiply_or_divide(z, x, dx, y, dy)
    return z, dz


def divide(x, dx, y, dy):
    """
    Calculate the division; z = x / y, with error uncertainty propagation.
    """
    z = np.divide(x, y) if y != 0 else math.inf
    dz = uncertainty_multiply_or_divide(z, x, dx, y, dy)

    return z, dz


def power(x, dx, y, dy):
    """
    Calculate the value; z = x^y, with error/uncertainty propagation.
    """
    z = np.power(x, y)

    dz_of_dx = np.multiply(np.multiply(y, z), np.divide(dx, x)) if dx != 0 else 0
    dz_of_dy = np.multiply(np.multiply(dy, z), np.log10(np.abs(x))) if dy != 0 else 0
    dz = np.sqrt(np.add(np.power(dz_of_dx, 2), np.power(dz_of_dy, 2)))
    return z, dz


def ln(x, dx=0):
    """
    Calculate the value; z = ln(x), with error/uncertainty propagation.
    """
    z = np.log(x)
    dz = np.divide(dx, x) if x != 0 and dx != 0 else 0
    return z, dz


def log10(x, dx=0):
    z = np.log10(x)
    dz = np.multiply(np.divide(dx, x), 0.434) if x != 0 and dx != 0 else 0
    return z, dz


def uncertainty_add_or_subtract(dx=0, dy=0):
    """
    Calculate the uncertainty associated with a sum or difference calc based on the passed error values.
    """
    dz_of_dx = np.power(dx, 2) if dx != 0 else 0
    dz_of_dy = np.power(dy, 2) if dy != 0 else 0
    dz = np.sqrt(np.add(dz_of_dx, dz_of_dy))
    return dz


def uncertainty_multiply_or_divide(z, x, dx, y, dy):
    """
    Calculate the uncertainty associated with a multiplication or division based on the passed value and error values.
    z will be the value resulting from the initial multiplication or division of x and y.
    """
    dz_of_dx = np.power(np.divide(dx, x), 2) if x != 0 and dx != 0 else 0
    dz_of_dy = np.power(np.divide(dy, y), 2) if y != 0 and dy != 0 else 0
    dz = np.multiply(np.sqrt(np.add(dz_of_dx, dz_of_dy)), z)
    return dz
