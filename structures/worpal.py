

class Worpal:
	def __init__(
			self,
			music_queue: dict,
			playing: dict,
			query: dict,
			mc_uuids: dict,
			secrets: dict
	):
		self.music_queue = music_queue
		self.playing = playing
		self.query = query
		self.mc_uuids = mc_uuids
		self.secrets = secrets
		self.color = 0x0b9ebc
		self.icon = "https://i.imgur.com/Rygy2KWs.jpg"