from gtksourceview import SourceBuffer

class CulebraBuffer(SourceBuffer):

    def __init__(self, filename=None):
        SourceBuffer.__init__(self)
        self.filename=filename
        self.current_line = 0
        self.connect('changed', self.update_cursor_position)   
        

    def update_cursor_position(self, buff):
        it = buff.get_iter_at_mark(buff.get_insert())
        self.current_line = buff.get_iter_at_mark(buff.get_insert()).get_line()
