import sublime_plugin, os, re
# Main drawbacks:
# * Only Makefile supported
# * No sticking to project defined paths (simply traverses the tree)
# * Always asks what to run, if there is more than one option (no quickrun)
class MakeTargetableExecCommand(sublime_plugin.WindowCommand):
	# Settings:
	# * what should be matched in makefile
	targetMatch = re.compile("^([a-z_]+):")
	# Session
	# * storage for per-buildfile "default" indexes
	instanceRunIndexes = {}

	def run(self, **kwargs):
		try:
			kwargs.pop("config") # reserved
		except KeyError:
			pass

		view = self.window.active_view()
		buildfile = self.get_nearest_buildfile(view.file_name())
		if not buildfile:
			return
		targets = self.enumerate_targets(buildfile)

		if len(targets) > 1:
			# Remember that this sh** is asynchronous, therefore drag all necessary data along.
			# Thereore, creating callback function each time seems necessary.
			def on_select(index):
				self.set_default_build_index(buildfile, index)
				self.quick_panel_callback(buildfile, targets, index, kwargs)
			self.window.show_quick_panel(targets, on_select, 0, self.get_default_build_index(buildfile))
		elif len(targets) == 1:
			self.quick_panel_callback(buildfile, targets, 0, kwargs)

	def get_nearest_buildfile(self, filename):
		dir, _ = os.path.split(filename)
		prevdir = None
		# @todo also stop on out-of-project
		while prevdir != dir:
			makefile = dir + os.sep + 'Makefile'
			if os.path.isfile(makefile):
				return makefile
			prevdir = dir
			dir = os.path.dirname(dir)

	def enumerate_targets(self, buildfile):
		fh = open(buildfile, 'r')
		targets = []
		for line in fh.readlines():
			match = self.targetMatch.search(line)
			if match:
				targets.append(match.group(1))
		fh.close()
		return targets

	def get_default_build_index(self, buildfile):
		# if self.runIndexPerView:
		# 	return view.settings().get('make_targetable_defidx', 0)
		# else:
		return self.instanceRunIndexes.get(buildfile, 0)

	def set_default_build_index(self, buildfile, index):
		if index == -1:
			return
		# if self.runIndexPerView:
		# 	view.settings().set('make_targetable_defidx', index)
		# else:
		self.instanceRunIndexes[buildfile] = index

	def quick_panel_callback(self, buildfile, targets, index, kwargs):
		if index == -1:
			return
		task = kwargs
		task.update({
			"cmd": ["make", targets[index]],
			"working_dir": os.path.dirname(buildfile)
		})
		self.window.run_command("exec", task)
