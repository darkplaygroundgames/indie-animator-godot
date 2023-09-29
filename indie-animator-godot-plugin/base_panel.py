import bpy
from bpy.props import StringProperty, IntProperty, BoolProperty, FloatProperty, FloatVectorProperty
from bpy.types import UIList

# pylint: disable=no-method-argument

class Base_Panel():
    bl_category = "Indie Animator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    props = []

    @staticmethod
    def _unregister(scene):
        if Base_Panel.props:
            for prop in Base_Panel.props:
                del prop

    @staticmethod
    def add_string(description, default=""):
        prop = StringProperty \
        (
            name = "",
            description = description,
            default = default
        )

        Base_Panel.props.append(prop)
        return prop

    @staticmethod
    def add_file_browser(description, default="", updateFn=None):
        prop = StringProperty \
        (
            name = "",
            description = description,
            default = default,
            subtype = "FILE_PATH",
            update=updateFn
        )

        Base_Panel.props.append(prop)
        return prop

    @staticmethod
    def add_folder_browser(description, default=""):
        prop = StringProperty \
        (
            name = "",
            description = description,
            default = default,
            subtype = "DIR_PATH"
        )

        Base_Panel.props.append(prop)
        return prop

    @staticmethod
    def add_checkbox(description, default=False, updateFn=None):
        prop = BoolProperty \
        (
            name = "",
            description = description,
            default = default,
            update=updateFn
        )

        Base_Panel.props.append(prop)
        return prop

    @staticmethod
    def add_int(min, max, default=0, updateFn=None):
        prop = IntProperty \
        (
            name = "",
            min = min,
            max = max,
            default = default,
            update=updateFn
        )

        Base_Panel.props.append(prop)
        return prop

    @staticmethod
    def add_float(min, max, default=0, updateFn=None):
        prop = FloatProperty \
        (
            name = "",
            min = min,
            max = max,
            default = default,
            update=updateFn
        )

        Base_Panel.props.append(prop)
        return prop

    @staticmethod
    def add_float_vector(min, max, size = 4, default = (1, 1, 1, 1), subtype='COLOR', updateFn=None):
        prop = FloatVectorProperty \
        (
            name = "",
            min = min,
            max = max,
            size = size,
            default = default,
            subtype = subtype,
            update=updateFn
        )

        Base_Panel.props.append(prop)
        return prop

    @staticmethod
    def add_list(layout, ui_list, scene, name, index):
        row = layout.row()
        row.template_list(
            ui_list,
            '',
            scene,
            name,
            scene,
            index)

    @staticmethod
    def edit_mode():
        return bpy.context.active_object.mode == 'EDIT'

    @staticmethod
    def add_control(context, layout, name, label, units = "", alignment = 'RIGHT', percentage = 0.5, parent = None):
        if parent:
            column = parent.column()
            column.prop(context.scene, name)
            return column

        split = layout.split(factor=percentage, align=True)
        if label != "":
            text, control = (split.column(), split.column())
            text.alignment = alignment
            text.label(text=label + ":")
        else:
            control = split.column()
        control.prop(context.scene, name)
        if units != "":
            unit = split.column()
            unit.label(text=units)
        return split

    @staticmethod
    def add_button(context, layout, operator, button_text, parent = None, percentage = 1.0):
        if parent:
            column = parent.column()
            column.operator(operator, text = button_text)
            return column

        if percentage == 1.0:
            row = layout.row()
            row.operator(operator, text = button_text)
            return row

        # Get the second column and add the button so we default to right aligned
        split = layout.split(factor=percentage, align=True)
        control = split.column()
        control = split.column()
        control.operator(operator, text = button_text)
        return split

    @staticmethod
    def add_spacer(context, layout):
        row = layout.row()
        row.separator()

    @staticmethod
    def add_label(context, layout, label, parent = None, alignment = 'LEFT'):
        if parent:
            row = parent.row()
        else:
            row = layout.row()
        row.alignment = alignment
        row.label(text=label)
        return row
