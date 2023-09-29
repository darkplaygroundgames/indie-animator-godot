
import os
import sys
import math
import shutil
import subprocess
import json
import time
import string
from pprint import pprint
from math import radians
import bmesh
import bpy
from enum import Enum
from bpy.props import StringProperty, IntProperty, BoolProperty
from bpy.types import UIList
import uuid
from . utils import *


def _get_id(ob):
    """
    Gets the id of the object.  If one doesn't exist one
    is created then the new id is returned
    """
    if not ob:
        return ''

    if "id" not in ob:
        ob["id"] = str(uuid.uuid4())

    return ob["id"]


class WIZ_OT_base_normal_map(bpy.types.Operator):
    bl_label = "Simple operator"
    bl_idname = "view3d.generate_normal_map"
    bl_description = "Generate a normal map"

    def _create_base_texture():
        ob = bpy.context.active_object
        base_material_name = _get_id(ob) + "_material"
        tex_image_name = _get_id(ob) + "_tex_image"
        base_texture_name = _get_id(ob) + "_base_texture"

        material = bpy.data.materials[base_material_name]
        bsdf = material.node_tree.nodes["Principled BSDF"]
        tree_nodes = material.node_tree.nodes
        images = bpy.data.images

        if tex_image_name in tree_nodes:
            texImage = tree_nodes[tex_image_name]
        else:
            texImage = tree_nodes.new('ShaderNodeTexImage')
            texImage.name = tex_image_name

        if base_texture_name in images:
            image = images[base_texture_name]
        else:
            image = bpy.data.images.new(
                base_texture_name,
                width=1024,
                height=1024,
                alpha=True,
                float_buffer=True)

        # Update the fill colour of the texture
        fill_colour = bpy.context.scene.texture_base_colour
        image_file = bpy.context.scene.base_texture_file
        if image_file:
            texImage.image = bpy.data.images.load(image_file, check_existing=True)
        else:
            image.pixels[:] = list(fill_colour) * image.generated_width * image.generated_height
            texImage.image = image

        material.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])


    def _create_base_material():
        scene = bpy.context.scene

        ob = bpy.context.active_object

        # Ensure there is a base material and texture
        base_material_name = _get_id(ob) + "_material"
        materials = bpy.data.materials
        if base_material_name in materials:
            material = materials[base_material_name]
        else:
            material = materials.new(name=base_material_name)
            material.use_nodes = True
            material.specular_intensity = 0
            material.specular_color = (1.0, 1.0, 1.0)
            material.diffuse_color = (1.0, 0, 0, 0)

        # Assign the base material to object
        if ob.data.materials:
            ob.data.materials[0] = material
        else:
            ob.data.materials.append(material)

        update_material_settings(None, None)

    def _create_normal_map():
        scene = bpy.context.scene
        selected_objects = bpy.context.selected_objects

        normal_map_width = 2048 if not scene.normal_map_width else scene.normal_map_width
        normal_map_height = 2048 if not scene.normal_map_height else scene.normal_map_height

        # Figure out which object is supposed to have the normal map (hint, its the low poly one)
        if len(selected_objects) == 2:
            if len(selected_objects[0].data.polygons) > len(selected_objects[1].data.polygons):
                low_poly = selected_objects[1]
            else:
                low_poly = selected_objects[0]
        elif len(selected_objects) == 1:
            low_poly = selected_objects[0]

        # Ensure there is a base material and texture
        base_material_name = _get_id(low_poly) + "_material"
        materials = bpy.data.materials
        if base_material_name in materials:
            material = materials[base_material_name]
        else:
            material = materials.new(name=base_material_name)
            material.use_nodes = True
            material.specular_intensity = 0
            material.specular_color = (1.0, 1.0, 1.0)
            material.diffuse_color = (1.0, 0, 0, 0)

        bsdf = material.node_tree.nodes["Principled BSDF"]

        # If the tex image already exists grab it.  Otherwise create a new one
        tree_nodes = material.node_tree.nodes
        tex_image_name = _get_id(low_poly) + "_normal_tex_image"
        if tex_image_name in tree_nodes:
            texImage = tree_nodes[tex_image_name]
        else:
            texImage = tree_nodes.new('ShaderNodeTexImage')
            texImage.name = tex_image_name

        # If the normal map image already exists grab it.  Otherwise create a new one
        normal_map_name = _get_id(low_poly) + "_normal_map"
        images = bpy.data.images
        if normal_map_name in images:
            image = images[normal_map_name]
        else:
            # Create the normal map texture
            image = bpy.data.images.new(
                normal_map_name,
                width=normal_map_width,
                height=normal_map_height,
                alpha=True,
                float_buffer=True)

        image.scale(normal_map_width, normal_map_height)

        texImage.image = image

        # If the new normal map node exists grab it, otherwise create a new one
        normal_map_node_name = _get_id(low_poly) + "_normal_map_node"
        nodes = material.node_tree.nodes
        if normal_map_node_name in nodes:
            normalMap = nodes[normal_map_node_name]
        else:
            normalMap = material.node_tree.nodes.new('ShaderNodeNormalMap')
            normalMap.name = normal_map_node_name

        normalMap.inputs[0].default_value = 0.5 if not scene.normal_map_strength else scene.normal_map_strength

        # Create links
        material.node_tree.links.new(normalMap.inputs['Color'], texImage.outputs['Color'])
        material.node_tree.links.new(normalMap.outputs['Normal'], bsdf.inputs['Normal'])

    def _generate_normal_texture():
        scene = bpy.context.scene
        selected_objects = bpy.context.selected_objects

        # Figure out which object is supposed to have the normal map (hint, its the low poly one)
        if len(selected_objects[0].data.polygons) > len(selected_objects[1].data.polygons):
            high_poly = selected_objects[0]
            low_poly = selected_objects[1]
        else:
            high_poly = selected_objects[1]
            low_poly = selected_objects[0]

        base_material_name = _get_id(low_poly) + "_material"
        material = bpy.data.materials[base_material_name]
        tree_nodes = material.node_tree.nodes

        tex_image_name = _get_id(low_poly) + "_normal_tex_image"
        texImage = tree_nodes[tex_image_name]

        # Ensure the correct texture is selected
        if not texImage.select:
            info("Please select the texture map texture node before baking")
            return

        # Select only the normal map texture
        for node in tree_nodes:
            node.select = False
        texImage.select = True


        # Setup some rendering settings so we can bake
        current_engine = scene.render.engine
        scene.render.engine = 'CYCLES'

        max_ray_distance = 0.05 if not scene.normal_map_ray_distance else scene.normal_map_ray_distance
        normal_map_width = 2048 if not scene.normal_map_width else scene.normal_map_width
        normal_map_height = 2048 if not scene.normal_map_height else scene.normal_map_height

        texImage.image.scale(normal_map_width, normal_map_height)

        bpy.ops.object.bake(
            type='NORMAL',
            #pass_filter={None},
            filepath='',
            width=normal_map_width,
            height=normal_map_height,
            margin=2,
            use_selected_to_active=True,
            max_ray_distance=max_ray_distance,
            cage_extrusion=0.0,
            cage_object='',
            normal_space='TANGENT',
            normal_r='POS_X',
            normal_g='POS_Y',
            normal_b='POS_Z',
            save_mode='INTERNAL',
            use_clear=True,
            use_cage=False,
            use_split_materials=False,
            use_automatic_name=False,
            uv_layer='')

        scene.render.engine = current_engine

        normal_map_name = _get_id(low_poly) + "_normal_map"
        image = bpy.data.images[normal_map_name]
        image.update()


class WIZ_OT_create_base_texture(WIZ_OT_base_normal_map):
    bl_idname = "view3d.create_base_texture"
    def execute(caller, context):
        # Ensure we have an object selected
        selected_objects = bpy.context.selected_objects
        if not selected_objects:
            info("Please select one object to create a blank base texture")
            return {'FINISHED'}

        WIZ_OT_base_normal_map._create_base_material()
        WIZ_OT_base_normal_map._create_base_texture()

        return {'FINISHED'}

class WIZ_OT_setup_normal_map(WIZ_OT_base_normal_map):
    bl_idname = "view3d.setup_normal_map"
    def execute(caller, context):
        # Ensure we have an object selected
        selected_objects = bpy.context.selected_objects
        if not selected_objects:
            info("Please select one object to create a blank normal map")
            return {'FINISHED'}

        # Create all nodes, images, materials and connect
        WIZ_OT_base_normal_map._create_base_material()
        WIZ_OT_base_normal_map._create_normal_map()

        return {'FINISHED'}


class WIZ_OT_generate_normal_map(WIZ_OT_base_normal_map):
    bl_idname = "view3d.generate_normal_map"
    def execute(caller, context):
        # Ensure we have at least 2 objects selected
        selected_objects = bpy.context.selected_objects
        if len(selected_objects) < 2:
            info("Please select high and low res objects (low res last)")
            return {'FINISHED'}

        WIZ_OT_base_normal_map._generate_normal_texture()

        return {'FINISHED'}

class WIZ_OT_generate_material(WIZ_OT_base_normal_map):
    bl_idname = "view3d.generate_material"
    def execute(caller, context):
        # Ensure we have an object selected
        selected_objects = bpy.context.selected_objects
        if len(selected_objects) != 1:
            info("Please select an object to add a material to")
            return {'FINISHED'}

        WIZ_OT_base_normal_map._create_base_material()

        return {'FINISHED'}

def _get_material(ob = None):
    if not ob:
        return None
        selected_objects = bpy.context.selected_objects

        # Get the selected object
        if not len(selected_objects) == 1:
            return None
        ob = selected_objects[0]

    return ob.active_material

    # Get the material
    base_material_name = _get_id(ob) + "_material"
    materials = bpy.data.materials
    if not base_material_name in materials:
        return None
    return materials[base_material_name]

def _get_bsdf(ob = None):
    material = _get_material(ob)
    if not material:
        return None

    return material.node_tree.nodes["Principled BSDF"]

def update_normal_map_strength(caller, context):
    scene = bpy.context.scene

    material = _get_material()
    if not material:
        return

    # Get the normal map if it exists and update the strength
    normal_map_node_name = _get_id(ob) + "_normal_map_node"
    nodes = material.node_tree.nodes
    if normal_map_node_name not in nodes:
        return
    normalMap = nodes[normal_map_node_name]
    normalMap.inputs[0].default_value = 0.5 if not scene.normal_map_strength else scene.normal_map_strength


def update_normal_map_ray_distance(caller, context):
    WIZ_OT_generate_normal_map.execute(caller, context)

def update_base_texture_settings(caller, context):
    if not len(bpy.context.selected_objects) == 1:
        return
    ob = bpy.context.selected_objects[0]
    base_texture_name = _get_id(ob) + "_base_texture"
    images = bpy.data.images

    # Update the fill colour of the texture or the texture file
    fill_colour = bpy.context.scene.texture_base_colour
    image_file = bpy.context.scene.base_texture_file
    if image_file:
        material = _get_material()
        if material:
            tree_nodes = material.node_tree.nodes
            tex_image_name = _get_id(ob) + "_tex_image"
            if tex_image_name in tree_nodes:
                texImage = tree_nodes[tex_image_name]
                texImage.image = bpy.data.images.load(image_file, check_existing=True)
    else:
        if base_texture_name in images:
            image = images[base_texture_name]
            image.pixels[:] = list(fill_colour) * image.generated_width * image.generated_height
            image.update()

def update_material_settings(caller, context):
    bsdf = _get_bsdf()
    if bsdf:
        bsdf.inputs['Base Color'].default_value = bpy.context.scene.texture_base_colour


def get_material_settings(ob):
    bsdf = _get_bsdf(ob)
    if bsdf:
        emission_colour = list(bsdf.inputs['Emission'].default_value)
        emission_strength = round(bsdf.inputs['Emission Strength'].default_value, 2)
        emission_enabled = emission_strength > 0 and emission_colour[0] + emission_colour[1] + emission_colour[2] + emission_colour[3] != 0
        return {
            'colour': bsdf.inputs['Base Color'].default_value,
            'metallic': round(bsdf.inputs['Metallic'].default_value, 2),
            'specular': round(bsdf.inputs['Specular'].default_value, 2),
            'roughness': 1.0 - round(bsdf.inputs['Roughness'].default_value, 2),
            'clearcoat': round(bsdf.inputs['Clearcoat'].default_value, 2),
            'emission': bsdf.inputs['Emission'].default_value,
            'emission_strength': emission_strength,
            'emission_enabled': emission_enabled,
        }
    return {}
