import random
from halibot import HalModule

class GameState():
	def __init__(self, channel, answer=None, users=None, size="4", max_attempts=10):
		self.channel = channel
		self.running = True

		if len(size) > 3 or int(size) > 10:
			raise Exception("Size is too large")
		self.answer = answer if answer else str(random.randint(10**(int(size)-1),(10**int(size))-1))
		self.attempts = 0
		self.max_attempts = int(max_attempts)
		if users:
			return  # TODO: remove this return when eval is gone
			self.users = eval(users)
			random.shuffle(self.users)
			self.nextuser = 0
		else:
			self.users = None

	def checkuser(self, user):
		if not self.users:
			return ""
		if user == self.users[self.nextuser]:
			self.nextuser += 1
			if self.nextuser == len(self.users):
				self.nextuser = 0
				random.shuffle(self.users)
			return " -- next up: " + self.users[self.nextuser]
		return None

	def getnextuser(self):
		return self.users[self.nextuser]

class MastermindModule(HalModule):

	def init(self):
		self.state = {}

	def receive(self, msg):
		if msg.body.startswith("!mind "):
			self.meta_commands(msg)
			return
		if not msg.body.startswith("#"):
			return
		s = self.state.get(msg.context.whom, None)
		if s and len(msg.body[1:]) == len(s.answer) and str.isdigit(msg.body[1:]):
			self.handle_attempt(msg, msg.body[1:], s)


	def meta_commands(self, msg):
		string = msg.body.split(" ")
		sby = "!"
		if len(string) == 1:
			return
		if string[1] == "start":
			if self.state.get(msg.context.whom):
				self.reply(msg, body="Game already started!")
				return
			args = self.parse_gameargs(string[2:])
			if "channel" not in args:
				args["channel"] = msg.context.whom
			else:
				msg.context.whom = args["channel"]
				sby = " by {}!".format(msg.author)

			try:
				self.state[args["channel"]] = GameState(**args)
			except Exception as e:
				self.reply(msg, body="Failed to start game: {}".format(str(e)))
				self.log.info("Failed to start game: {}".format(str(e)))
				return
			self.reply(msg, body="Game started" + sby)
			if self.state[args["channel"]].users:
				self.reply(msg, body="First up: {}".format(self.state[args["channel"]].users[0]))
				
		elif string[1] in ("stop", "end"):
			if self.state.get(msg.context.whom):
				self.end_game(msg, self.state.get(msg.context.whom))
				return
			self.reply(msg, body="Game not running...")
			return
		else:
			self.reply(msg, body="Unknown command '{}'".format(string[1]))
	
	def parse_gameargs(self, ls):
		ret = {}
		for l in ls:
			try:
				a,b = l.split(":")
				ret[a] = b
			except:
				pass
		return ret

	def handle_attempt(self, msg, ans, state):
		hits = 0
		blows = 0

		nextup = state.checkuser(msg.author)
		if nextup == None:
			return

		state.attempts += 1

		if ans == state.answer:
			self.end_game(msg, state, victory=True)
			return

		t1 = []
		t2 = []
		for i in range(len(ans)):
			t1.append(ans[i]) if ans[i] != state.answer[i] else None
			t2.append(state.answer[i]) if ans[i] != state.answer[i] else None
		hits = len(state.answer) - len(t1)

		for t in t1:
			if t in t2:
				t2.remove(t)
		blows = len(state.answer) - hits - len(t2)

		self.reply(msg, body="Attempt #{} -- Hits: {}, Blows: {}".format(state.attempts, hits, blows) + nextup)
		if state.attempts == state.max_attempts:
			self.end_game(msg, state)
			return

	def end_game(self, msg, state, victory=False):
			state.running = False
			self.state[state.channel] = None
			if victory:
				self.reply(msg, body="DING DING DING!!! Correct answer of {} found on attempt #{}".format(state.answer, state.attempts))
				return
			self.reply(msg, body="Game over! Answer was: {}".format(state.answer))
