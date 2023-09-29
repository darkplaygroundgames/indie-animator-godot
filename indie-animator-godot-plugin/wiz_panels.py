import os
import colorsys
import webbrowser
from .base_panel import Base_Panel
import bpy
from bpy.types import Menu, Operator, UIList, AddonPreferences
import bl_operators
from bl_operators.presets import AddPresetBase
from . wiz_utils import (
    PALETTE_TYPE,
    PALETTE_TYPE_COLOUR_COUNT,
    WIZ_MT_palette_set_mono,
    WIZ_MT_palette_set_complimentary,
    WIZ_MT_palette_set_analogous,
    WIZ_MT_palette_set_triadic,
)
from . normal_maps import (
    update_normal_map_strength,
    update_normal_map_ray_distance,
    update_base_texture_settings,
)
from . animations import import_animations, edit_animation

# pylint: disable=no-method-argument


def object_change_callback(*arg):
    scene = bpy.context.scene
    selected_object = bpy.context.active_object

    # godot Settings Tab
    mass = selected_object.get("godot_mass", None)
    drag = selected_object.get("godot_drag", None)
    if mass is not None:
        scene.godot_mass = mass
    if drag is not None:
        scene.godot_drag = drag


class WIZ_PT_wiz_warning_panel(bpy.types.Panel, Base_Panel):
    bl_idname = "WIZ_PT_wiz_warning_panel"
    bl_label = "Select an object for more options"

    @classmethod
    def poll(cls, context):
        return not context.selected_objects

    def register():
        pass

    def unregister():
        Base_Panel._unregister(bpy.types.Scene)

    def draw(self, context):
        pass


class WIZ_PT_OpenURLOperator(bpy.types.Operator):
    bl_idname = "wm.open_url"
    bl_label = "Open URL"
    bl_description = "https://patreon.com/DarkPlaygroundGames"

    def execute(self, context):
        webbrowser.open("https://patreon.com/DarkPlaygroundGames")
        return {'FINISHED'}




class WIZ_PT_wiz_3D_export_details(bpy.types.Panel, Base_Panel):
    bl_idname = "WIZ_PT_wiz_3D_export_details"
    bl_label = "Export Details"

    @classmethod
    def poll(cls, context):
        ob = context.selected_objects
        collection = bpy.context.view_layer.active_layer_collection
        return ob or collection

    def register():
        scene = bpy.types.Scene
        scene.scene_export_destination = Base_Panel.add_folder_browser(
            description="The destination folder to place the 3D exports",
            default="")
        scene.godot_prefab_path = Base_Panel.add_string("Path to the godot Prefabs Folder", "")
        scene.auto_godot_folder_setup = Base_Panel.add_checkbox("Create a godot folder structure based\non the collection hierarchy in Blender", False)

    def unregister():
        Base_Panel._unregister(bpy.types.Scene)

    def draw(self, context):
        scene = bpy.context.scene
        layout = self.layout
        if scene.scene_export_destination:
            name = scene.scene_export_destination.replace("\\", "/").rstrip("/").split("/")[-1]
            self.add_label(context, self.layout, f"Game Project Location ({name}):", alignment = 'LEFT')
        else:
            self.add_label(context, self.layout, "Select a Project:", alignment = 'LEFT')
        self.add_control(context, layout, "scene_export_destination", "", percentage=1.0)
        self.add_spacer(context, layout)

        if scene.scene_export_destination:
            self.add_label(context, self.layout, f"Prefabs Location:", alignment = 'LEFT')
            self.add_control(context, layout, "godot_prefab_path", "", percentage=1, alignment = 'RIGHT')
            self.add_control(context, layout, 'auto_godot_folder_setup', 'Auto Hierarchy', percentage=0.75)


class WIZ_PT_wiz_3D_exports(bpy.types.Panel, Base_Panel):
    bl_idname = "WIZ_PT_wiz_3D_exports"
    bl_label = "Export to Godot"

    @classmethod
    def poll(cls, context):
        ob = context.selected_objects
        collection = bpy.context.view_layer.active_layer_collection
        return ob or collection

    def register():
        scene = bpy.types.Scene

    def unregister():
        Base_Panel._unregister(bpy.types.Scene)

    def draw(self, context):
        scene = bpy.context.scene
        layout = self.layout
        if scene.scene_export_destination:
            row = self.add_button(context, layout, 'view3d.export_glb_individual', 'Individual')
            self.add_button(context, layout, 'view3d.export_glb_collection', 'Collection', row)
        else:
            self.add_label(context, layout, "Select a Game project for more options", alignment = 'LEFT')



class WIZ_PT_wiz_material(bpy.types.Panel, Base_Panel):
    bl_idname = "WIZ_PT_wiz_material"
    bl_label = "Materials"
    bl_space_type = 'VIEW_3D'
    bl_context = "objectmode"

    @classmethod
    def poll(cls, context):
        ob = context.selected_objects
        return ob

    @staticmethod
    def update_palette_colours(self, context):
        scene = bpy.context.scene
        primary = (
            scene.palette_primary[0],
            scene.palette_primary[1],
            scene.palette_primary[2],
            scene.palette_primary[3]
        )
        if bpy.types.Scene.palette_type == PALETTE_TYPE.MONOCHROMATIC.value:
            pass
        elif bpy.types.Scene.palette_type == PALETTE_TYPE.COMPLIMENTARY.value:
            bpy.types.Scene.palette_secondary_1 = Base_Panel.add_float_vector(
                0,
                1.0,
                default=(
                    1.0 - primary[0],
                    1.0 - primary[1],
                    1.0 - primary[2],
                    primary[3],
                )
            )
        elif bpy.types.Scene.palette_type == PALETTE_TYPE.ANALOGOUS.value:
            adj1, adj2 = adjacent_colors(primary[0], primary[1], primary[2], primary[3], 30)
            bpy.types.Scene.palette_secondary_1 = Base_Panel.add_float_vector(
                0,
                1.0,
                default=adj1
            )
            bpy.types.Scene.palette_secondary_2 = Base_Panel.add_float_vector(
                0,
                1.0,
                default=adj2
            )
        elif bpy.types.Scene.palette_type == PALETTE_TYPE.TRIADIC.value:
            adj1, adj2 = adjacent_colors(primary[0], primary[1], primary[2], primary[3], 120)
            bpy.types.Scene.palette_secondary_1 = Base_Panel.add_float_vector(
                0,
                1.0,
                default=adj1
            )
            bpy.types.Scene.palette_secondary_2 = Base_Panel.add_float_vector(
                0,
                1.0,
                default=adj2
            )

    def register():
        scene = bpy.types.Scene

        scene.mat_type_mode = bpy.props.EnumProperty(
            name = "",
            description = "Choose Material Type",
            items = [
                ("Basic", "Basic Texture", ""),
                ("Load", "Load Texture", ""),
                ("Pallette", "Pallette", ""),
            ]
        )

        # Normal Map Controls
        scene.normal_map_strength = Base_Panel.add_float(0, 10.0, 0.5, updateFn=update_normal_map_strength)
        scene.normal_map_ray_distance = Base_Panel.add_float(0, 1.0, 0.05, updateFn=update_normal_map_ray_distance)
        scene.normal_map_width = Base_Panel.add_int(512, 4096, 2048)
        scene.normal_map_height = Base_Panel.add_int(512, 4096, 2048)

        # Palette Controls
        bpy.types.Scene.palette_type = PALETTE_TYPE.ANALOGOUS.value
        scene.palette_primary = Base_Panel.add_float_vector(0, 1.0, default=(0,0,1,1), updateFn=WIZ_PT_wiz_material.update_palette_colours)
        scene.palette_secondary_1 = Base_Panel.add_float_vector(0, 1.0, default=(0,0.5,1,1))
        scene.palette_secondary_2 = Base_Panel.add_float_vector(0, 1.0, default=(0.5,0,1,1))
        scene.palette_secondary_3 = Base_Panel.add_float_vector(0, 1.0)
        scene.pallette_pixel_size = Base_Panel.add_int(1, 64, 32)
        scene.allow_transparency = Base_Panel.add_checkbox("Allow Alpha", False)

        # Base Texture Controls
        scene.texture_base_colour = Base_Panel.add_float_vector(0, 1.0, default=(0,0,0,1), updateFn=update_base_texture_settings)
        scene.base_texture_file = Base_Panel.add_file_browser(
            description="Optional source base texture image",
            updateFn=update_base_texture_settings)


    def unregister():
        Base_Panel._unregister(bpy.types.Scene)

    def draw(self, context):
        layout = self.layout
        scene = bpy.types.Scene
        selected_object = bpy.context.active_object

        self.add_control(context, layout, "mat_type_mode", "", percentage=1.0)

        if context.scene.mat_type_mode == "Pallette":
            split = layout.split(factor=0.5, align=True)
            control = split.column()
            control = split.column()
            control.menu("WIZ_MT_palette_type_select_menu", text=bpy.types.Scene.palette_type)

            num_colours = PALETTE_TYPE_COLOUR_COUNT[bpy.types.Scene.palette_type]
            self.add_control(context, layout, "palette_primary", "Primary")
            if num_colours > 1:
                self.add_control(context, layout, "palette_secondary_1", "Accent")
            if num_colours > 2:
                self.add_control(context, layout, "palette_secondary_2", "Accent")
            if num_colours > 3:
                self.add_control(context, layout, "palette_secondary_3", "Accent")
            self.add_control(context, layout, "pallette_pixel_size", "Pixel Size")
            image_width = bpy.context.scene.pallette_pixel_size * 16
            self.add_label(context, layout, f"Image size: {image_width}x{image_width} pixels", alignment = 'RIGHT')
            #self.add_control(context, layout, 'allow_transparency', 'Allow Alpha')
            self.add_button(context, layout, 'view3d.draw_pallet', 'Create', percentage=0.5)

        elif context.scene.mat_type_mode == "Load":
            self.add_control(context, layout, "base_texture_file", "File")
            self.add_button(context, layout, 'view3d.create_base_texture', 'Load', percentage=0.5)

        elif context.scene.mat_type_mode == "Basic":
            self.add_control(context, layout, "texture_base_colour", "Base Colour")
            self.add_button(context, layout, 'view3d.generate_material', 'Create', percentage=0.5)

        # Normal Map Settings
        #self.add_spacer(context, layout)
        #self.add_spacer(context, layout)
        #self.add_label(context, self.layout, "NORMAL MAP (Experimental):", alignment = 'LEFT')
        #self.add_spacer(context, layout)
        #self.add_control(context, layout, "normal_map_width", "Width")
        #self.add_control(context, layout, "normal_map_height", "Height")
        #self.add_control(context, layout, "normal_map_strength", "Strength", percentage=0.5)
        #self.add_control(context, layout, "normal_map_ray_distance", "Ray Distance", percentage=0.5)
        #row = self.add_button(context, layout, 'view3d.setup_normal_map', 'Create')
        #self.add_button(context, layout, 'view3d.generate_normal_map', 'Bake', row)


class WIZ_MT_palette_type_select_menu(bpy.types.Menu):
    bl_idname = "WIZ_MT_palette_type_select_menu"
    bl_label = "Select"

    def draw(self, context):
        self.layout.operator("view3d.palette_mono", text=WIZ_MT_palette_set_mono.palette_type)
        self.layout.operator("view3d.palette_complimentary", text=WIZ_MT_palette_set_complimentary.palette_type)
        self.layout.operator("view3d.palette_analogous", text=WIZ_MT_palette_set_analogous.palette_type)
        self.layout.operator("view3d.palette_triadic", text=WIZ_MT_palette_set_triadic.palette_type)

def adjacent_colors(r, g, b, a, d):
    d = d / 360
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    h = [(h+d) % 1 for d in (-d, d)]
    adjacent1 = colorsys.hls_to_rgb(h[0], l, s) + (a,)
    adjacent2 = colorsys.hls_to_rgb(h[1], l, s) + (a,)
    return (adjacent1, adjacent2)



class WIZ_PT_wiz_armature_panel(bpy.types.Panel, Base_Panel):
    bl_idname = "WIZ_PT_wiz_armature_panel"
    bl_label = "Armature"
    bl_space_type = 'VIEW_3D'

    def register():
        scene = bpy.types.Scene
        scene.collider_offset = Base_Panel.add_float(-100, 100.0, 0)


    def unregister():
        Base_Panel._unregister(bpy.types.Scene)

    def draw(self, context):
        layout = self.layout

        self.add_label(context, self.layout, "Type:")
        row = self.add_button(context, layout, 'view3d.add_armature_human', 'Human')
        self.add_button(context, layout, 'view3d.add_armature_quadruped', 'Animal', row)
        self.add_button(context, layout, 'view3d.add_armature_generic', 'Generic')
        #row = self.add_button(context, layout, 'view3d.add_armature_door', 'Door')
        #self.add_button(context, layout, 'view3d.add_armature_double_door', 'Double Door', row)

        self.add_label(context, self.layout, "Rigify:")
        row = self.add_button(context, layout, 'view3d.add_rigify_basic_human', 'Basic Human')
        self.add_button(context, layout, 'view3d.add_rigify_basic_quadruped', 'Quaruped', row)
        row = self.add_button(context, layout, 'view3d.add_rigify_human', 'Human')
        self.add_button(context, layout, 'view3d.add_rigify_bird', 'Bird', row)
        row = self.add_button(context, layout, 'view3d.add_rigify_cat', 'Cat')
        self.add_button(context, layout, 'view3d.add_rigify_horse', 'Horse', row)
        row = self.add_button(context, layout, 'view3d.add_rigify_shark', 'Shark')
        self.add_button(context, layout, 'view3d.add_rigify_wolf', 'Wolf', row)

        self.add_label(context, self.layout, "Action:")
        row = self.add_button(context, layout, 'view3d.symeterize_armature', 'Symeterize')
        self.add_button(context, layout, 'view3d.parent_armature', 'Assign', row)
        #self.add_button(context, layout, 'view3d.set_t_pose', 'TPose', percentage=0.5)


class WIZ_PT_wiz_animation_panel(bpy.types.Panel, Base_Panel):
    bl_idname = "WIZ_PT_wiz_animation_panel"
    bl_label = "Animations"
    bl_space_type = 'VIEW_3D'

    def register():
        scene = bpy.types.Scene
        scene.animation_file = Base_Panel.add_file_browser(description="Load Animation File", updateFn=import_animations)
        scene.edit_animation_file = Base_Panel.add_file_browser(description="Load Animation File", updateFn=edit_animation)

    def unregister():
        Base_Panel._unregister(bpy.types.Scene)

    def draw(self, context):
        layout = self.layout

        self.add_control(context, layout, "animation_file", "Load Animation", percentage=0.75, alignment = 'LEFT')
        self.add_control(context, layout, "edit_animation_file", "Edit Animation", percentage=0.75, alignment = 'LEFT')
        self.add_button(
            context,
            layout,
            'view3d.play_animation',
            'Stop' if bpy.context.screen.is_animation_playing else 'Play',
            percentage=0.5)


class WIZ_PT_wiz_donation_panel(bpy.types.Panel, Base_Panel):
    bl_idname = "WIZ_PT_wiz_donation_panel"
    bl_label = "Support Dark Playground Games"
    bl_space_type = 'VIEW_3D'

    def register():
        scene = bpy.types.Scene

    def unregister():
        Base_Panel._unregister(bpy.types.Scene)

    def draw(self, context):
        layout = self.layout
        self.add_button(context, layout, 'wm.open_url', 'Donate')
