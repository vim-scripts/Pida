import gtk
special_chars = (" ", "\n", ".", ":", ",", "'", 
                '"', "(", ")", "{", "}", "[", "]")

def wordcount(b):
    i1 = b.get_start_iter()
    
    i2 = i1.copy()
    i2.forward_word_end()

    i = 0

    while i2.get_offset() <> i1.get_offset():
        i += 1
        i1 = i2.copy()
        i2.forward_word_end()
    
    return i

def buffer_wordlist(b):
    i1 = b.get_start_iter()
    
    i2 = i1.copy()
    i2.forward_word_end()

    wl = []
    
    i1, i2 = b.get_bounds()
    
    text = b.get_text(i1, i2)
        
    text = text.replace("\n", " ")
    text = text.replace(",", " ")
    text = text.replace(".", " ")
    text = text.replace(":", " ")
    text = text.replace("(", " ")
    text = text.replace(")", " ")
    text = text.replace("'", " ")
    text = text.replace('"', " ")
    b = gtk.TextBuffer()
    b.set_text(text)

    i1 = b.get_start_iter()
    
    i2 = i1.copy()
    i2.forward_word_end()

    while i2.get_offset() <> i1.get_offset():
        
        

        word = b.get_text(i1, i2).strip()

        #print word

        if not word in wl:
            wl.append(word)
            
        i1 = i2.copy()
        i2.forward_word_end()

    return wl

def text_wordlist(text):

    for i in special_chars:
        text = text.replace(i, " ")
    wl = text.split(" ")
    
    wl = [x for x in wl if x != '']
    
    return wl
    
if __name__ == "__main__":

    b = gtk.TextBuffer()
    
    print text_wordlist("veo un marciano sentado en el ala de un vuelo de taca en un dia como el de hoy")
    
