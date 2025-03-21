
from fonticon_fa6 import FA6S
import superqt.fonticon
from superqt.fonticon import icon as qticon
from superqt.fonticon._plugins import discover, FontIconManager

print("Font location:", FA6S.__font_file__)

from qtpy.QtWidgets import QApplication

from importlib.metadata import EntryPoint, entry_points

entries = entry_points()
print("ENTRIES:", entries)
# if hasattr(entries, "select"):  # python>3.10
#     print("USING SELECT")
_entries1 = entries.select(group='superqt.fonticon')
# else:
#     print("USING OLD WAY")
_entries2 = entries.get('superqt.fonticon', [])

print("ENTRIES 1:", _entries1)
print("ENTRIES 2:", _entries2)

app = QApplication([])
discover()

print("FONT PLUGINS:", FontIconManager._PLUGINS)
icon = qticon(FA6S.floppy_disk)


print('!!!!!FLOPPY ', icon)



# Rebuild the path manually from the bundled directory
# with importlib.resources.path("fonticon_fa6.fonts", "Font Awesome 6 Free-Solid-900.otf") as font_path:
#     FA6S.__font_file__ = str(font_path)
