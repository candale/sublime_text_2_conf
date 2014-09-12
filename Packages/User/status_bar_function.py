import sublime_plugin

class StatusBarFunctionCommand(sublime_plugin.TextCommand):
   def run(self, edit):
      view = self.view
      region = view.sel()[0]
      functionRegs = view.find_by_selector('meta.procedure')
      for r in reversed(functionRegs):
         if r.a < region.a:
            view.set_status('function', view.substr(r))
            return
      view.erase_status('function')