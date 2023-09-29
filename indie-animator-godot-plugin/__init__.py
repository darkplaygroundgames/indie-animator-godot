
bl_info = {
    "name" : "Indie Animator Godot",
    "author" : "Dark Playground Games",
    "description" : "Export rigged models and animations to Godot.",
    "blender" : (3, 4, 1),
    "version" : (1, 0, 1),
    "location" : "View3D",
    "warning" : "",
    "category" : "Generic"
}

import bpy
import inspect

from . wiz_panels import *
from . wiz_armature import *
from . wiz_utils import *
from . animations import *
from . normal_maps import *
from . utils import *

# Generate a class list to register with blender but don't include base classes
classes = [class_member for name, class_member in inspect.getmembers(sys.modules[__name__], inspect.isclass)
    if name.startswith("WIZ_") and not name.startswith("WIZ_OT_base_")
]

register, unregister = bpy.utils.register_classes_factory(classes)
