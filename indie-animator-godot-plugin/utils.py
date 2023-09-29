import os
import bpy
import addon_utils

def info(message = "", title = "Warning", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text = message)

    print(message)
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

def _get_path(path):
    return os.path.abspath(bpy.path.abspath(path))


def get_godot_project_path():
    return _get_path(bpy.context.scene.scene_export_destination)

def get_godot_prefabs_path(collection, collection_selected, file = ""):
    parts = f"{bpy.context.scene.godot_prefab_path}/{_get_hierarchy(collection, not collection_selected)}".replace("\\", "/").split("/")
    parts = list(filter(None, parts))
    if len(parts) <= 1:
        path = os.path.join(get_godot_project_path(), bpy.context.scene.godot_prefab_path, file)
    else:
        path = get_godot_project_path()
        for part in parts:
            path = os.path.join(path, part)
        path = os.path.join(path, file)
    create_folders(path)
    return path

def get_godot_textures_path(file = ""):
    parts = bpy.context.scene.godot_texture_path.replace("\\", "/").split("/")
    if len(parts) <= 1:
        path = os.path.join(get_godot_project_path(), bpy.context.scene.godot_texture_path, file)
    else:
        path = get_godot_project_path()
        for part in parts:
            path = os.path.join(path, part)
        path = os.path.join(path, file)
    create_folders(path)
    return path


def get_texture_paths():
    images = [image for image in bpy.data.images if image.users > 0 and image.name != "Render Result"]

    # Unpack images
    for image in images:
        if image.type == 'IMAGE' and image.packed_file:
            image.unpack()

    return [os.path.normpath(bpy.path.abspath(img.filepath)) for img in images]

def get_user_path():
    # Ensure the user folder exists
    path = os.path.join(
        bpy.utils.resource_path("USER").split("blender")[0],
        "darkplaygroundgames",
        "indieanimator",
        os.path.basename(os.path.normpath(bpy.context.scene.scene_export_destination))
    )
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    return path

def create_folders(path):
    folder = os.path.dirname(path)
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)

def _get_collection_path(collection, target_collection, include_current_collection):
    if collection == target_collection:
        if include_current_collection:
            return collection.name
        return "/"

    for child in collection.children:
        path = _get_collection_path(child, target_collection, include_current_collection)
        if path:
            return f"{collection.name}/{path}"

    return ""

def _get_hierarchy(target_collection, include_current_collection):
    if not bpy.context.scene.auto_godot_folder_setup:
        return ""

    collections = [collection for collection in bpy.data.collections]
    path = ""
    for collection in collections:
        p = _get_collection_path(collection, target_collection, include_current_collection)
        if len(p) > len(path):
            path = p

    return path

def set_object_mode() -> str:
    """
    Sets the current mode to object mode.  Returns the last mode before we changed it.
    """
    if bpy.context.active_object:
        last_mode = bpy.context.active_object.mode
        if bpy.context.active_object.mode == 'EDIT':
            bpy.ops.object.editmode_toggle()
        elif bpy.context.active_object.mode == 'POSE':
            bpy.ops.object.posemode_toggle()
        return last_mode
    return ""

def set_pose_mode() -> str:
    """
    Sets the current mode to pose mode.  Returns the last mode before we changed it.
    """
    if bpy.context.active_object:
        last_mode = bpy.context.active_object.mode
        if  bpy.context.active_object.mode != 'POSE':
            bpy.ops.object.posemode_toggle()
        return last_mode
    return ""

def set_edit_mode() -> str:
    """
    Sets the current mode to edit mode.  Returns the last mode before we changed it.
    """
    if bpy.context.active_object:
        last_mode = bpy.context.active_object.mode
        if  bpy.context.active_object.mode != 'EDIT':
            bpy.ops.object.editmode_toggle()
        return last_mode
    return ""

def set_mode(mode: str):
    """
    Sets the current mode to pose mode.  Returns the last mode before we changed it.
    """
    if mode == 'POSE':
        set_pose_mode()
    elif mode == 'EDIT':
        set_edit_mode()
    elif mode == 'OBJECT':
        set_object_mode()

def clear_transformations():
    """
    Sets the pose mode and clears all transformations to set to a t-pose position
    then sets back to the previous mode.
    """
    last_mode = set_pose_mode()
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.transforms_clear()
    bpy.ops.pose.armature_apply(selected=False)
    set_mode(last_mode)

def normalize_pose_animation(arm):
    """
    Moves a tpose or apose animation to the bottom of the animation list so it will
    show in godot as the default pose in the editor
    """
    if arm and arm.type == "ARMATURE" and arm.animation_data:
        # Find a pose animation
        for track in arm.animation_data.nla_tracks:
            if "pose" in track.name.lower():
                area = bpy.context.area.type
                bpy.context.area.type = 'NLA_EDITOR'
                bpy.ops.anim.channels_select_all(action='DESELECT')
                track.select = True
                bpy.ops.anim.channels_move(direction='BOTTOM')
                bpy.context.area.type = area

def get_object_collection(ob):
    for collection in bpy.data.collections:
        for obj in collection.objects:
            if ob == obj:
                return collection
    return None

def select_collection(collection):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in collection.objects:
        ob.select_set(True)
    for layer_collection in bpy.context.view_layer.layer_collection.children:
        if layer_collection.collection == collection:
            bpy.context.view_layer.active_layer_collection = layer_collection
            return


class WIZ_OT_fracture_object(bpy.types.Operator):
    bl_label = "Simple operator"
    bl_idname = "view3d.fracture_object"
    bl_description = "Fracture the selected object"

    def execute(caller, context):
        """
        Fractures each selected object
        """
        set_object_mode()

        objects = bpy.context.selected_objects
        for object in objects:
            if object.type == "MESH":
                WIZ_OT_fracture_object.fracture(object)

        return {'FINISHED'}

    def fracture(obj):
        """
        Fractures an object
        """
        try:
            if not obj.data.materials or not len(obj.data.materials) > 1:
                info(f"({obj.name}) Please add a second material for the inner fracture texture")
                return

            # Remove from a collection if already linked
            collection = get_object_collection(obj)
            if collection:
                collection.objects.unlink(obj)
            if obj.name in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.unlink(obj)

            # Create a collection to handle the new breakable
            collection = bpy.data.collections.new(obj.name)
            bpy.context.scene.collection.children.link(collection)

            # Add the object to the collection
            collection.objects.link(obj)

            # Deselect all objects and then reselect in the new collection
            select_collection(collection)

            # Enable the Cell Fracture add-on
            #bpy.ops.wm.addon_enable(module='fracture')

            # Set the cell fracture settings
            bpy.ops.object.add_fracture_cell_objects(source={'PARTICLE_OWN'},
                source_limit=bpy.context.scene.fracture_limit,
                source_noise=bpy.context.scene.fracture_noise,
                cell_scale=(1, 1, 1),
                recursion=0,
                recursion_source_limit=8,
                recursion_clamp=250,
                recursion_chance=0.25,
                recursion_chance_select='SIZE_MIN',
                use_smooth_faces=False,
                use_sharp_edges=True,
                use_sharp_edges_apply=True,
                use_data_match=True,
                use_island_split=True,
                margin=0.001,
                material_index=1,
                use_interior_vgroup=False,
                mass_mode='VOLUME',
                mass=1,
                use_recenter=True,
                use_remove_original=True,
                collection_name="",
                use_debug_points=False,
                use_debug_redraw=True,
                use_debug_bool=False)

            # Mark the main node as a breakable, set the collider and add physics as defaults
            obj["breakable"] = "ON"
            obj["collider"] = "BOX"
            obj["physics"] = "ON"

        except AttributeError:
            info("Please enable the cell fracture plugin first")
