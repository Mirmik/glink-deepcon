import glink.util

class GlinkCore:
	def __init__(self):
		self.targets = {}

core = GlinkCore()

class Target:
	def __init__(self, tgt, deps, **kwargs):
		self.depends = set()
		self.tgt = tgt

		for d in deps:
			self.depends.add(d)
		
		for k, v in kwargs.items():
			setattr(self, k, v)

	def invoke(self, func):
		if (isinstance(func ,str)):
			res = getattr(self, func, None)
			if (res == None):
				return None
			ret = res(self)
			return ret
		else:
			return func(self)

	def __repr__(self):
		return "target:"+self.tgt

def target(tgt, deps=[], **kwargs):
	core.targets[tgt] = Target(tgt=tgt, deps=deps, **kwargs)

def get_target(tgt):
	if tgt in core.targets:
		return core.targets[tgt]
	print("Попытка получить несуществующую цель: {0}".format(tgt))
	exit(-1)

def depends_as_set(tgt, incroot=True):
	res = set()
	if incroot:
		res.add(tgt)
	
	target = get_target(tgt)
	
	for d in target.depends:
		if not d in res:
			res.add(d)
			subres = depends_as_set(d)
			res = res.union(subres)
	return res

def invoke_foreach(func):
	save = dict(core.targets)
	for k, v in save.items():
		v.invoke(func)

class SubTree:
	def __init__(self, root):
		self.root = root
		self.depset = depends_as_set(root)

	def update(self):
		SubTree.__init__(self, root)

	def invoke_foreach(self, ops, cond=None):
		sum = 0
		ret = None

		for d in self.depset:
			target = get_target(d)
			if cond==None:
				ret = target.invoke(ops)
			else:
				if cond(self, target):
					ret = target.invoke(ops)
			
			if ret != None:
				sum+=1
	
		return sum	

	def __generate_rdepends_lists(self, targets):
		for t in targets:
			t.rdepends = []
			t.rcounter = 0
	
		for t in targets:
			for dname in t.depends:
				dtarget = get_target(dname)
				dtarget.rdepends.append(t.tgt)
	
	
	def reverse_recurse_invoke(self, ops, cond=glink.util.always_true):
		targets = [get_target(t) for t in self.depset]
		sum = 0
	
		self.__generate_rdepends_lists(targets)
		
		works = glink.util.queue()
	
		for t in targets:
			if t.rcounter == len(t.depends):
				works.put(t)
	
		while(not works.empty()):
			w = works.get()
	
			if cond(self, w):
				ret = w.invoke(ops)
				if not (ret == 0 or ret == None):
					raise context.ResultIsNotNull()
				if ret == 0:
					sum += 1
	
			for r in [get_target(t) for t in w.rdepends]:
				r.rcounter = r.rcounter + 1
				if r.rcounter == len(r.depends):
					works.put(r)
	
		return sum

def subtree(root):
	return SubTree(root)