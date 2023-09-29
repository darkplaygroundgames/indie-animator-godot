import os
import sys
import math
import shutil
import subprocess
import json
import time
import string
from math import fabs, pi
from mathutils import Vector
from pprint import pprint
from math import radians
from pathlib import Path
import bmesh
import bpy
from enum import Enum
from bpy.props import StringProperty, IntProperty, BoolProperty
from bpy.types import UIList
import uuid
from . utils import *

from . draw import create_gradient_pallet

class StateSnapshot():
    def __init__(self):
        self.selected_objects = bpy.context.selected_objects
        self.mode = get_object_mode()
        self.last_cursor_pos = Vector(bpy.context.scene.cursor.location)
        self.pivot_point = bpy.context.scene.tool_settings.transform_pivot_point

    def Restore(self):
        bpy.context.scene.cursor.location = self.last_cursor_pos
        bpy.context.scene.tool_settings.transform_pivot_point = self.pivot_point
        bpy.ops.object.select_all(action='DESELECT')
        for obj in self.selected_objects:
            obj.select_set(True)
        restore_mode(self.mode)


class PALETTE_TYPE(Enum):
    MONOCHROMATIC = 'Monochromatic'
    COMPLIMENTARY = 'Complimentary'
    ANALOGOUS = 'Analogous'
    TRIADIC = 'Triadic'

PALETTE_TYPE_COLOUR_COUNT = {
    PALETTE_TYPE.MONOCHROMATIC.value: 1,
    PALETTE_TYPE.COMPLIMENTARY.value: 2,
    PALETTE_TYPE.ANALOGOUS.value: 3,
    PALETTE_TYPE.TRIADIC.value: 3,
}

def get_object_mode():
    if bpy.context.active_object:
        return bpy.context.active_object.mode
    return None

def restore_mode(mode):
    if mode and bpy.context.active_object and mode != bpy.context.active_object.mode:
        if mode in ('EDIT', 'OBJECT'):
            bpy.ops.object.editmode_toggle()
        elif mode in ('POSE', 'OBJECT'):
            bpy.ops.object.posemode_toggle()

def set_edit_mode():
    if bpy.context.active_object and not bpy.context.active_object.mode == 'EDIT':
        bpy.ops.object.editmode_toggle()

def text_to_mesh():
    mode = get_object_mode()
    set_edit_mode()
    bpy.ops.object.convert(target='MESH')
    restore_mode(mode)

def add_material(prim, name, colour):
    materials = bpy.data.materials
    if not name in materials:
        # Add a new material
        bpy.ops.material.new()
        material = materials[-1]
        material.name = name

    material = bpy.data.materials[name]
    prim.data.materials.append(material)
    material.diffuse_color = colour
    return len(list(materials)) - 1


class WIZ_OT_export_glb_individual(bpy.types.Operator):
    bl_label = "Simple operator"
    bl_idname = "view3d.export_glb_individual"
    bl_description = "Export selected individual objects to Godot in a glb file"

    def execute(caller, context):
        if not bpy.data.filepath:
            info("Please save your blend file first")
            return {'FINISHED'}

        scene = bpy.context.scene

        # If we are in edit mode switch to object mode
        set_object_mode()

        if not WIZ_OT_export_glb_individual.update_selection():
            return {'FINISHED'}

        state = StateSnapshot()

        if bpy.context.view_layer.objects.active:
            WIZ_OT_export_glb_individual.export_individual(scene)

        state.Restore()

        return {'FINISHED'}

    def export_individual(scene):
        # Export each object individually
        for obj in bpy.context.selected_objects:
            # Select only the object we want to export
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)

            # Export
            _export_glb(scene, obj, obj.users_collection[0], False)


    def update_selection():
        selected_objects = bpy.context.selected_objects
        if selected_objects:
            for ob in selected_objects:
                if ob.type == "ARMATURE":
                    info("Items with an armature must be exported as a collection")
                    return False
            return True

        collection = bpy.context.collection
        if collection and len(collection.all_objects) > 0:
            bpy.ops.object.select_all(action='DESELECT')
            for ob in collection.all_objects:
                if ob.type == "ARMATURE":
                    info("Items with an armature must be exported as a collection")
                    return False

            bpy.context.view_layer.objects.active = None

            # Select all items in the collection
            if not selected_objects:
                for ob in collection.all_objects:
                    ob.select_set(True)
                    bpy.context.view_layer.objects.active = ob

            return True

        info("Collection seems to be empty")
        return False




class WIZ_OT_export_glb_collection(bpy.types.Operator):
    bl_label = "Simple operator"
    bl_idname = "view3d.export_glb_collection"
    bl_description = "Export a selected collection to Godot in a glb file"

    def execute(caller, context):
        if not bpy.data.filepath:
            info("Please save your blend file first")
            return {'FINISHED'}

        # If we are in edit mode switch to object mode
        set_object_mode()

        if not WIZ_OT_export_glb_collection.update_selection():
            return {'FINISHED'}

        scene = bpy.context.scene

        state = StateSnapshot()

        if bpy.context.view_layer.objects.active:
            if not WIZ_OT_export_glb_collection.check_config():
                        info("Please don't export armature objects with non-armature objects")
                        return {'FINISHED'}
            WIZ_OT_export_glb_collection.export_collection(scene)

        state.Restore()

        return {'FINISHED'}

    def export_collection(scene):
        # Use the collection name as the name of the glb file.  If none exists use a default name.
        ob = bpy.context.active_object
        #collection = bpy.context.view_layer.active_layer_collection
        collection = ob.users_collection[0]
        if not collection:
            info("Please select something in a collection")
            return {'FINISHED'}

        bpy.ops.object.select_all(action='DESELECT')
        for obj in collection.all_objects:
            obj.select_set(True)

        bpy.ops.view3d.snap_cursor_to_center()

        bpy.context.scene.tool_settings.transform_pivot_point = 'CURSOR'

        # Export
        _export_glb(scene, collection, collection, True)

        bpy.ops.object.select_all(action='DESELECT')

        # Reset the active object to something.  We do this to ensure we can
        # hit the export button without reselecting something
        #bpy.context.view_layer.objects.active = collection.all_objects[0]


    def check_config():
        # Look at the objects that are selected.  If we have a mix
        # of armature type and non-armature type return False as we
        # don't want them to mix, otherwise True
        arm_exists = False
        non_arm_exists = False
        collection = bpy.context.collection
        if collection:
            for ob in collection.all_objects:
                if ob.type == "ARMATURE":
                    arm_exists = True
                elif ob.type == "MESH" and ob.parent == None:
                    non_arm_exists = True

        return not (arm_exists and non_arm_exists)

    def update_selection():
        selected_objects = bpy.context.selected_objects
        if not selected_objects:
            collection = bpy.context.collection
            if collection and len(collection.all_objects) > 0:
                for ob in collection.all_objects:
                    if ob.type == "ARMATURE":
                        bpy.ops.object.select_all(action='DESELECT')
                        ob.select_set(True)
                        bpy.context.view_layer.objects.active = ob
                        return True

                bpy.context.view_layer.objects.active = None

                # Select all items in the collection
                if not selected_objects:
                    for ob in collection.all_objects:
                        ob.select_set(True)
                        bpy.context.view_layer.objects.active = ob
                return True
        else:
            collection = bpy.context.active_object.users_collection[0]

        # Check the collection for anything that has an armature.  If
        # one is found we want to export as a collection.  If not, we
        # return an error
        if collection and len(collection.all_objects) > 0:
            for ob in collection.all_objects:
                if ob.type == "ARMATURE":
                    bpy.ops.object.select_all(action='DESELECT')
                    ob.select_set(True)
                    bpy.context.view_layer.objects.active = ob

            # Select all items in the collection
            if not selected_objects:
                for ob in collection.all_objects:
                    ob.select_set(True)

            return True

        info("Collection seems to be empty")
        return False


    def use_individual_export():
        selected_objects = bpy.context.selected_objects
        if not selected_objects:
            collection = bpy.context.collection
            if collection:
                for ob in collection.all_objects:
                    if ob.type == "ARMATURE":
                        bpy.ops.object.select_all(action='DESELECT')
                        ob.select_set(True)
                        bpy.context.view_layer.objects.active = ob
                        return False

                bpy.context.view_layer.objects.active = None

                # Select all items in the collection
                if not selected_objects:
                    for ob in collection.all_objects:
                        ob.select_set(True)
                        bpy.context.view_layer.objects.active = ob
            return False
        else:
            collection = bpy.context.active_object.users_collection[0]

        # Check the collection for anything that has an armature.  If
        # one is found we want to export as a collection.  If not, we
        # want to export individual
        if collection:
            for ob in collection.all_objects:
                if ob.type == "ARMATURE":
                    bpy.ops.object.select_all(action='DESELECT')
                    ob.select_set(True)
                    bpy.context.view_layer.objects.active = ob
                    return False

            # Select all items in the collection
            if not selected_objects:
                for ob in collection.all_objects:
                    ob.select_set(True)

        return True


def _get_center(collection):
    # Look at all the objects in the collection.  If this is a large
    # collection that lays over the world origin we don't want to move
    # anything.  This is because large objects are generally levels we
    # don't want changing the zero point on every slight change.  Otherwise
    # we want to find the center of all the objects in the collection
    # to allow us to move it to the world origin so in Godot there won't
    # be an offset between its location and the center of the object.
    # If there is an armature we just use the location of the armature instead

    # If there is only one thing in the collection we can just use the location of it
    if len(collection.all_objects) == 1:
        ob = collection.all_objects[0]
        return (ob.location.x, ob.location.y, ob.location.z)

    leftX = None
    rightX = None
    forwardY = None
    backY = None
    for ob in collection.all_objects:
        if ob.type == "ARMATURE":
            return (ob.location.x, ob.location.y, ob.location.z)
        if not leftX or leftX > ob.location.x:
            leftX = ob.location.x
        if not rightX or rightX < ob.location.x:
            rightX = ob.location.x
        if not forwardY or forwardY < ob.location.y:
            forwardY = ob.location.y
        if not backY or backY > ob.location.y:
            backY = ob.location.y
    # If the world origin is within the collection and the collection is big
    # enough return 0 so it will not move
    width = rightX - leftX
    gurth = forwardY - backY
    if width > 5 and gurth > 5 and leftX <= 0 and rightX >= 0 and forwardY >= 0 and backY <= 0:
        return (0, 0, 0)

    # Return the center of the objects.  Always assume the z is correct
    centerX = leftX + width / 2
    centerY = backY + gurth / 2
    return (centerX, centerY, 0)

def _export_glb(scene, obj, collection, collection_selected):
    scene = bpy.context.scene
    if obj.hide_viewport == False:
        extension = "glb"
        dest = get_godot_prefabs_path(collection, collection_selected, f"{obj.name.lower()}.{extension}")

        arm_exists = False
        if collection and collection_selected:
            for ob in collection.all_objects:
                if ob.type == "ARMATURE":
                    normalize_pose_animation(ob)
                    arm_exists = True
                    break

        # Move the object to the 0, 0 point
        if collection_selected:
            last_location = _get_center(collection)
        else:
            last_location = obj.location
        inv_location = (-last_location[0], -last_location[1], -last_location[2])
        bpy.ops.transform.translate(
            value=inv_location,
            orient_axis_ortho='X',
            orient_type='GLOBAL',
            orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
            orient_matrix_type='GLOBAL',
            mirror=False,
            use_proportional_edit=False,
            proportional_edit_falloff='SMOOTH',
            proportional_size=1,
            use_proportional_connected=False,
            use_proportional_projected=False,
            snap=False, snap_elements={'INCREMENT'},
            use_snap_project=False,
            snap_target='CLOSEST',
            use_snap_self=True,
            use_snap_edit=True,
            use_snap_nonedit=True,
            use_snap_selectable=False)
        last_location = (-inv_location[0], -inv_location[1], -inv_location[2])


        # Rotate all the selected objects so they will face the correct direction
        if not arm_exists:
            bpy.ops.transform.rotate(
                value=pi,
                orient_axis='Z',
                orient_type='GLOBAL',
                orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                orient_matrix_type='GLOBAL',
                constraint_axis=(False, False, True),
                mirror=False,
                use_proportional_edit=False,
                proportional_edit_falloff='SMOOTH',
                proportional_size=1,
                use_proportional_connected=False,
                use_proportional_projected=False)

        # Remove any unused actions so they don't show in the final glb
        for action in bpy.data.actions:
            if action.users == 0 and not action.use_fake_user:
                bpy.data.actions.remove(action)

        bpy.ops.export_scene.gltf(
            filepath=dest,
            export_format='GLB',
            export_image_format='AUTO',
            export_texture_dir='',
            export_materials='EXPORT',
            export_colors=True,
            export_normals=True,
            export_cameras=False,
            export_lights=False,
            export_force_sampling=False,
            export_extras=True,
            use_selection=True,  # Export only selected objects
            export_yup=True,  # Change to True if your model has Y-up orientation
            export_apply=False,  # Apply modifiers (set to True if needed)
            export_animations=True,
            export_anim_single_armature=True,
            #export_animation_mode='NLA_TRACKS',
        )

        # Clear any bone transformations so our model ends up in a rest pose
        #if arm_exists:
        #    clear_transformations()

        # Rotate the selected objects back to what they were
        if not arm_exists:
            bpy.ops.transform.rotate(
                value=pi,
                orient_axis='Z',
                orient_type='GLOBAL',
                orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                orient_matrix_type='GLOBAL',
                constraint_axis=(False, False, True),
                mirror=False,
                use_proportional_edit=False,
                proportional_edit_falloff='SMOOTH',
                proportional_size=1,
                use_proportional_connected=False,
                use_proportional_projected=False)

        # Move the object back to the previous point
        bpy.ops.transform.translate(
            value=last_location,
            orient_axis_ortho='X',
            orient_type='GLOBAL',
            orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
            orient_matrix_type='GLOBAL',
            mirror=False,
            use_proportional_edit=False,
            proportional_edit_falloff='SMOOTH',
            proportional_size=1,
            use_proportional_connected=False,
            use_proportional_projected=False,
            snap=False, snap_elements={'INCREMENT'},
            use_snap_project=False,
            snap_target='CLOSEST',
            use_snap_self=True,
            use_snap_edit=True,
            use_snap_nonedit=True,
            use_snap_selectable=False)


def update_text_size(caller, context):
    selected_objects = bpy.context.selected_objects
    if not selected_objects:
        info("Please select an object first")
        return
    updated = False
    for ob in selected_objects:
        if ob.type == 'FONT':
            ob.data.size = bpy.context.scene.ui_object_size
            updated = True
    if updated:
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')


def update_text_thickness(caller, context):
    selected_objects = bpy.context.selected_objects
    if not selected_objects:
        info("Please select an object first")
        return
    updated = False
    for ob in selected_objects:
        if ob.type == 'FONT':
            ob.data.extrude = bpy.context.scene.ui_object_thickness
            updated = True
    if updated:
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')


class WIZ_OT_set_object_center(bpy.types.Operator):
    bl_label = "Simple operator"
    bl_idname = "view3d.set_object_center"
    bl_description = "Set the center point of the object"

    def execute(caller, context):
        selected_objects = bpy.context.selected_objects
        if not selected_objects:
            info("Please select an object first")
            return {'FINISHED'}
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
        return {'FINISHED'}


class WIZ_OT_set_t_pose(bpy.types.Operator):
    bl_label = "Simple operator"
    bl_idname = "view3d.set_t_pose"
    bl_description = "Reset the armature bones to their default"

    def execute(caller, context):
        mode = bpy.context.active_object.mode
        set_pose_mode()
        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.pose.rot_clear()
        bpy.ops.pose.loc_clear()
        bpy.ops.pose.scale_clear()

        # If we are in edit mode switch to object mode
        restore_mode(mode)
        return {'FINISHED'}


class WIZ_OT_ready_generation(bpy.types.Operator):
    bl_label = "Simple operator"
    bl_idname = "view3d.ready_generation"
    bl_description = "Switch to the Texture Paint workspace and setup some view settings"


    def execute(caller, context):
        bpy.context.window.workspace = bpy.data.workspaces['Texture Paint']
        return {'FINISHED'}



class WIZ_OT_draw_pallet(bpy.types.Operator):
    bl_label = "Draw Pallet"
    bl_idname = "view3d.draw_pallet"
    bl_description = "Draw a low res pallet texture to the selected plane"

    def execute(caller, context):
        # Mark the mode as modify so the next resolution button press will change
        # the resolution of the current object rather than creating a new one
        if not bpy.data.filepath:
            info("Please save your blend file first")
            return {'FINISHED'}

        ob = bpy.context.active_object
        scene = bpy.context.scene

        material = bpy.data.materials.new(name="pallet")
        material.use_nodes = True
        material.specular_intensity = 0
        material.specular_color = (1.0, 1.0, 1.0)
        material.diffuse_color = (1.0, 0, 0, 0)
        bsdf = material.node_tree.nodes["Principled BSDF"]
        texImage = material.node_tree.nodes.new('ShaderNodeTexImage')
        texImage.interpolation = 'Linear'
        material.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])

        num_colours = PALETTE_TYPE_COLOUR_COUNT[bpy.types.Scene.palette_type]
        primary_colours = list(scene.palette_primary)
        secondary_colours = []

        if num_colours > 1:
            secondary_colours.append(list(scene.palette_secondary_1))
        if num_colours > 2:
            secondary_colours.append(list(scene.palette_secondary_2))
        if num_colours > 3:
            secondary_colours.append(list(scene.palette_secondary_3))

        gradient = create_gradient_pallet(
            f"{ob.name}_base_texture",
            primary_colours,
            secondary_colours,
           scene.pallette_pixel_size)

        if gradient:
            texImage.image = gradient

            # Assign it to object
            if ob.data.materials:
                ob.data.materials[0] = material
            else:
                ob.data.materials.append(material)

        return {'FINISHED'}


class base_palette_menu(bpy.types.Operator):
    bl_label = "Palette Menu"
    selected = PALETTE_TYPE.MONOCHROMATIC

class WIZ_MT_palette_set_mono(base_palette_menu):
    bl_idname = "view3d.palette_mono"
    palette_type = PALETTE_TYPE.MONOCHROMATIC.value

    def execute(caller, context):
        bpy.types.Scene.palette_type = PALETTE_TYPE.MONOCHROMATIC.value
        return {'FINISHED'}

class WIZ_MT_palette_set_complimentary(base_palette_menu):
    bl_idname = "view3d.palette_complimentary"
    palette_type = PALETTE_TYPE.COMPLIMENTARY.value

    def execute(caller, context):
        bpy.types.Scene.palette_type = PALETTE_TYPE.COMPLIMENTARY.value
        return {'FINISHED'}

class WIZ_MT_palette_set_analogous(base_palette_menu):
    bl_idname = "view3d.palette_analogous"
    palette_type = PALETTE_TYPE.ANALOGOUS.value

    def execute(caller, context):
        bpy.types.Scene.palette_type = PALETTE_TYPE.ANALOGOUS.value
        return {'FINISHED'}

class WIZ_MT_palette_set_triadic(base_palette_menu):
    bl_idname = "view3d.palette_triadic"
    palette_type = PALETTE_TYPE.TRIADIC.value

    def execute(caller, context):
        bpy.types.Scene.palette_type = PALETTE_TYPE.TRIADIC.value
        return {'FINISHED'}
