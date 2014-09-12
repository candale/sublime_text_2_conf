import sublime, sublime_plugin, re

class TreeCommand(sublime_plugin.TextCommand):
	def_pat = re.compile("(?i)[\s\t]*procedure\s.+:")
	call_pat = re.compile("(?i).*\s+run\s+[A-Za-z_\-0-9]+")
	main_block_pat = re.compile("(?i)[\s\t]*&ANALYZE-SUSPEND.*Main-Block\s+Procedure")
	end_prc_pat = re.compile("[\s\t]*&ANALYZE-RESUME[\s\t]*")
	call_value_pat = re.compile("(?i).*[\s\t]*run\s+value[\s\t]*\(.*\).*")
	result_str = ""

	def run(self, edit):
		# get the current view
		curr_window = self.view.window()
		# crate a new view
		new_view = curr_window.new_file()
		# give the new view focus
		curr_window.focus_view(new_view)

		# get all text on current view
		text = self.view.substr(sublime.Region(0, self.view.size()))
		# format text so it can pr processed correclty
		formated_text = self.format_text(text)

		# in case we have an error here, it means that the text we're processing
		# does not meet some requirements (e.g. doe not have a Main Block)
		try:
			# extract all procedures and calls to procedures from file
			temp_result = self.process_text(formated_text)
		except:
			new_view.insert(edit, 0, "Current file does not meet the structure requirements (e.g. does not have a main block)")
			return

		if "Main Block" not in temp_result:
			return

		# sort procedures in the order they appeared in the file
		temp_result = self.sort_procedures(temp_result)
		# print the result
		self.print_result(temp_result, temp_result["Main Block"], 1)

		# insert the result into the new view
		#new_view.insert(edit, 0, str(temp_result))
		new_view.insert(edit, 0, self.result_str)
		new_view.insert(edit, 0, "Main Block\n")


	def sort_procedures(self, tree):
		# sort the tree {"prc_name" : (prc_number, "prc_name"), ...}
		new_tree = dict()
		for key in tree:
			new_tree[key] = sorted(tree[key])

		return tree


	def print_result(self, tree, node, ident):
		for prc in node:
			self.result_str = self.result_str + ident * "   " + node[prc] + "\n"
			if node[prc] in tree:
				self.print_result(tree, tree[node[prc]], ident + 1)


	def format_text(self, text):
		# remove all string from the source
		text_without_strings= re.sub("[\"'].*[\"']", "", text)
		# remove all comments from the source
		text_without_comments = re.sub("/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+/", "", text_without_strings)
		# remove all empty lines
		text_without_empty_lines_final = re.sub("\n[\s\t]*\n", "\n", text_without_comments)

		return text_without_empty_lines_final



	def process_text(self, text):
		temp_result = dict()
		# flags that indicate if we passed main block, if we are in main block or if we are in a procedure (line wise)
		pass_main_block = in_main_block = in_prc = False
		# current procedure we are in
		cur_region = ""
		k = 0
		procedure_order = 0

		# for each line in text
		for line_str in text.split("\n"):
			# if Main Block begins
			if self.main_block_pat.match(line_str):
				in_main_block = True
				cur_region = "Main Block"
				temp_result["Main Block"] = dict()
				continue
			# if the current lines corresponds to procedure call
			elif self.call_pat.match(line_str):
				# if it is a simple call (RUN procedure_name)
				if self.call_value_pat.match(line_str):
					prc_name = re.sub("(?i).*[\t\s]+run\s+", "", line_str)
					prc_name = re.findall("(?i)value[\s\t]*\(.*\)", prc_name)[0]
				# if it is a value call (RUN VALUE("prc_name"))
				else:
					prc_name = re.sub("(?i).*[\t\s]+run\s+", "", line_str)
					prc_name = re.findall("[\w]+", prc_name)[0]

				# put the result in tmp_result which has the following structure : {"prc_name" : (call_number_in_current_procedure, "called_procedure_name"), ...}
				temp_result[cur_region][procedure_order] = prc_name
				procedure_order += 1 
			# if the current line represents a procedure header definition
			elif self.def_pat.match(line_str):
				prc_name = re.sub("(?i)[\s\t]*procedure\s+", "", line_str)
				prc_name = re.sub("\s*:\s*", "", prc_name)

				# if the the found procedure definition does not exist, create new entry in tmp_result with it's name
				if prc_name not in temp_result:
					temp_result[prc_name] = dict()

				in_main_block = False
				in_prc = True
				cur_region = prc_name
			# if the current line represents the end of a procedure. Reset flags
			elif self.end_prc_pat.match(line_str):
				procedure_order = 0
				in_main_block = False
				in_prc = False
				cur_region = None

		return temp_result