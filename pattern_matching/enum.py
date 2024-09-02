# coding: utf-8

"""
Author:		Sten Vercamman
			Univeristy of Antwerp

Example code for paper: Efficient model transformations for novices
url: http://msdl.cs.mcgill.ca/people/hv/teaching/MSBDesign/projects/Sten.Vercammen

The main goal of this code is to give an overview, and an understandable
implementation, of known techniques for pattern matching and solving the
sub-graph homomorphism problem. The presented techniques do not include
performance adaptations/optimizations. It is not optimized to be efficient
but rather for the ease of understanding the workings of the algorithms.
The paper does list some possible extensions/optimizations.

It is intended as a guideline, even for novices, and provides an in-depth look
at the workings behind various techniques for efficient pattern matching.
"""

class Enum(object):
	"""
	Custom Enum object for compatibility (enum is introduced in python 3.4)
	Usage create	: a = Enum(['e0', 'e1', ...])
	Usage call		: a.e0
	"""
	def __init__(self, args):
		next	= 0
		for arg in args:
			self.__dict__[arg] = next
			next	+= 1