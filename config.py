from configparser import ConfigParser

class Config:
	def __init__(self, config_path):
		self.config_path = config_path
		self.config = ConfigParser()
		self.config.read(config_path)

	def get(self, section, key, fallback=None):
		self.config.read(self.config_path)
		value = self.config.get(section, key, fallback=fallback)
		return value

	def getint(self, section, key, fallback=None):
		self.config.read(self.config_path)
		value = self.config.getint(section, key, fallback=fallback)
		return value

	def getboolean(self, section, key, fallback=None):
		self.config.read(self.config_path)
		value = self.config.getboolean(section, key, fallback=fallback)
		return value

	def set(self, section, key, value):
		key = str(key)
		value = str(value)

		self.config.read(self.config_path)

		if not (section in self.config.sections()):
			self.config[section] = {}

		self.config[section][key] = value

		with open(self.config_path, 'w') as conf:
			self.config.write(conf)

	def has_section(self, section):
		if section in self.config.sections():
			return True
		else:
			return False