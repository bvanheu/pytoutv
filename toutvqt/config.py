from PyQt4.Qt import QDir
from PyQt4.Qt import QSettings

class QTouTvConfig:
	DEFAULT_DOWNLOAD_DIRECTORY = QDir.home().absoluteFilePath("Tou.Tv")

	def __init__(self):
		self._fill_defaults()
		self.config_dict = self.defaults.copy()
		self._read_settings()

	def _fill_defaults(self):
		"""Fills defaults with sensible default values."""
		self.defaults = {}
		self.defaults['files/download_directory'] = QTouTvConfig.DEFAULT_DOWNLOAD_DIRECTORY
		self.defaults['network/http_proxy'] = None

	def _write_settings(self):
		settings = QSettings()
		settings.clear()

		for k in self.config_dict:
			if self.config_dict[k] != self.defaults[k]:
				settings.setValue(k, self.config_dict[k])

	def _read_settings(self):
		settings = QSettings()

		keys = settings.allKeys()

		for k in keys:
			self.config_dict[k] = settings.value(k)

	def debug_print_config(self):
		print(self.config_dict)
