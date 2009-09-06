"""
This module contains Helper constructs

This module is a part of the program Kupfer, see the main program file for
more information.
"""

import weakref

class WeakCallback (object):
	"""A Weak Callback object that will keep a reference to
	the connecting object with weakref semantics.

	This allows to connect to gobject signals without it keeping
	the connecting object alive forever.

	Will use @gobject_token or @dbus_token if set as follows:
		sender.disconnect(gobject_token)
		dbus_token.remove()
	"""
	def __init__(self, mcallback):
		"""Create a new Weak Callback calling the method @mcallback"""
		obj = mcallback.im_self
		attr = mcallback.im_func.__name__
		self.wref = weakref.ref(obj, self.object_deleted)
		self.callback_attr = attr
		self.gobject_token = None
		self.dbus_token = None

	def __call__(self, *args, **kwargs):
		obj = self.wref()
		if obj:
			attr = getattr(obj, self.callback_attr)
			attr(*args, **kwargs)
		elif self.gobject_token:
			sender = args[0]
			sender.disconnect(self.gobject_token)
			self.gobject_token = None

	def object_deleted(self, wref):
		if self.dbus_token:
			self.dbus_token.remove()
			self.dbus_token = None

def gobject_connect_weakly(sender, signal, mcallback, *user_args):
	"""Connect weakly to GObject @sender's @signal,
	with a callback method @mcallback
	"""
	wc = WeakCallback(mcallback)
	wc.gobject_token = sender.connect(signal, wc, *user_args)