class EventSample(object):
    callbacks = None
	
    def on(self, EHname, callback):
        if self.callbacks is None:
            self.callbacks = {}
	
        if EHname not in self.callbacks:
            self.callbacks[EHname] = [callback]
        else:
            self.callbacks[EHname].append(callback)
	
    def trigger(self, EHname):
        if self.callbacks is not None and EHname in self.callbacks:
            for callback in self.callbacks[EHname]:
                callback(self)
	
class MClass(EventSample):
    def __init__(self, mess):
        self.mess = mess
	
    def __str__(self):
        return "Message from other class: " + repr(self.mess)
	
def echo(text):
    print(text)
	
MC = MClass("Sample text")
MC.on("sample_event", echo)
MC.trigger("sample_event")