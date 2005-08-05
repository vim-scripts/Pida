
PIDA - README.txt

Welcome!


Requirements
--

1. Vim 6.3+
2. Python
3. Python-GTK2 (and GTK2)
4. Python-vte (and lib-vte)
5. Bicycle repair man (for Python features)
6. Gazpacho (for GTK RAD)

These are all commonly available in Linux distributions, but may have slightly
different names. You do not require to use, run or have heard of Gnome.

Installation
--

Enter the source directory, and issue the command:

    python setup.py install

(note: you will need to have root access if you are installing a system wide
copy.)


Upgrading
--

It is advised to remove old installations of Pida if upgrading from version
0.1.* to version 0.2.*. To achieve this automatically, please use the command:

    python setup.py upgrade

This will prompt you as to whether you want to remove previous Pida
installations.

Running
--

Execute the command

    pida

Extra Platform Notes
--

FBSD

To install the Python bindings for the vte library, please modify or override the
variable "CONFIGURE_ARGS= --disable-python" to something more like
--enable-python and make the port. (If you are a FBSD user please tell us if
this works, and provide us with better instructions. Thanks.)


Known Issues
--

1. Metacity

For unknown reasons, when using the Metacity window manager, with Vim
configured to use graphical dialog boxes, Vim appears to freeze with the
message ":confirm e /file/path". In fact, what has happened is that the
graphical dialog box has been sent to the very back of all the windows on your
current desktop, and is waiting to be clicked.

There s an easy fix, and that is to configure Vim to use console dialogs ":set
guioptions+=c".

2. Gdk-WARNING 

On running Pida, you may see this warning repeatedly:

Gdk-WARNING **: gdk_property_get(): length value has wrapped in calculation
(did you pass G_MAXLONG?)

This is caused by the VTE terminal widget, to test it, open a Python terminal
and execute:

>>> import vte
>>> vte.Terminal()

You will see the same warnings.

Note that these warnings appear to be harmless, and the terminal emulator
functions as normal. This happens in Debian Sid/Etch and you can find further
information at the bugreport of the issue: http://bugs.debian.org/316940

Bugs
--

You must must must please please please report bugs. It is simple, and quick
and by far the most useful thing anyone can do (except fix it!) if they discover one.
Even a quick email to aafshar@gmail.com will be enough.


Feature requests
--

I am always happy to listen to feature requests. Because of the pluggable
nature of Pida, it is easy to extend with plugins.


Enjoy!


Ali

aafshar@gmail.com
