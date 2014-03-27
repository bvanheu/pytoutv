from PyQt4.Qt import QDir
from PyQt4.Qt import QSettings
from PyQt4 import QtCore
from PyQt4 import Qt

class QTouTvConfig(Qt.QObject):
	DEFAULT_DOWNLOAD_DIRECTORY = QDir.home().absoluteFilePath("Tou.Tv")

	def __init__(self):
		super(QTouTvConfig, self).__init__()
		self._fill_defaults()

		# config_dict starts with the default
		self.config_dict = self.defaults.copy()
		self.config_item_changed.connect(self.tmp)

	config_item_changed = QtCore.pyqtSignal(str, object)

	def _fill_defaults(self):
		"""Fills defaults with sensible default values."""
		self.defaults = {}
		self.defaults['files/download_directory'] = QTouTvConfig.DEFAULT_DOWNLOAD_DIRECTORY
		self.defaults['network/http_proxy'] = None

	def write_settings(self):
		settings = QSettings()
		settings.clear()

		for k in self.config_dict:
			if self.config_dict[k] != self.defaults[k]:
				settings.setValue(k, self.config_dict[k])

	def read_settings(self):
		settings = QSettings()
		read_config = {}
		keys = settings.allKeys()

		for k in keys:
			read_config[k] = settings.value(k)

		self.apply_config(read_config)

	def apply_config(self, new_config):
		for key in new_config:
			new_value = new_config[key]
			if key in self.config_dict:
				if new_value != self.config_dict[key]:
					# Value changed
					self.config_item_changed.emit(key, new_value)
			else:
				# New config key
				self.config_item_changed.emit(key, new_value)
			self.config_dict[key] = new_config[key]

		self.write_settings()


	def debug_print_config(self):
		print(self.config_dict)

	def tmp(self, k, v):
		print("%s changed to %s" % (k, v))
