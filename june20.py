import bpy
import json
import math
import os

# Class for creating a wall
class Wall:
    def __init__(self, name, location, scale, rotation, color):
        self.name = name
        self.location = location
        self.scale = scale
        self.rotation = rotation
        self.color = color
        self.object = self.create_wall()

    def create_wall(self):
        bpy.ops.mesh.primitive_plane_add(size=2, location=self.location)
        wall = bpy.context.object
        wall.name = self.name
        wall.scale[0] = self.scale[0]
        wall.scale[1] = self.scale[1]
        wall.rotation_euler = self.rotation
        self.apply_material(wall)
        return wall

    def apply_material(self, wall):
        mat = bpy.data.materials.new(name=self.name + "_Material")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs['Base Color'].default_value = (*self.color, 1)  # RGB color with alpha 1
        if wall.data.materials:
            wall.data.materials[0] = mat
        else:
            wall.data.materials.append(mat)

    def add_cutout(self, cutout_object, operation='DIFFERENCE'):
        bpy.context.view_layer.objects.active = self.object
        bpy.ops.object.modifier_add(type='BOOLEAN')
        boolean_mod = self.object.modifiers[-1]
        boolean_mod.operation = operation
        boolean_mod.object = cutout_object
        bpy.ops.object.modifier_apply(modifier=boolean_mod.name)

    def shade_smooth(self):
        self.object.select_set(True)
        bpy.ops.object.shade_smooth()

# Class for creating a door or window cutout
class Cutout:
    def __init__(self, name, location, scale):
        self.name = name
        self.location = location
        self.scale = scale
        self.object = self.create_cutout()

    def create_cutout(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=self.location)
        cutout = bpy.context.object
        cutout.name = self.name
        cutout.scale[0] = self.scale[0]
        cutout.scale[1] = self.scale[1]
        cutout.scale[2] = self.scale[2]
        return cutout

# Class for creating a door or window
class DoorWindow:
    def __init__(self, wall, name, location, scale, material):
        self.wall = wall
        self.cutout = Cutout(name, location, scale)
        self.add_door_window(material)

    def add_door_window(self, material):
        self.wall.add_cutout(self.cutout.object)
        self.cutout.object.data.materials.append(material)
        self.wall.shade_smooth()

# Class for creating a door/window material
class DoorMaterial:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.material = self.create_material()

    def create_material(self):
        mat = bpy.data.materials.new(name=self.name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs['Base Color'].default_value = (*self.color, 1)  # RGB color with alpha 1
        return mat

# Class for creating furniture
class Furniture:
    def __init__(self, name, model_path, location, scale, rotation):
        self.name = name
        self.model_path = model_path
        self.location = location
        self.scale = scale
        self.rotation = rotation
        self.object = self.import_furniture()
        self.apply_material()

    def import_furniture(self):
        if self.model_path.lower().endswith('.blend'):
            return self.import_blender_furniture()
        elif self.model_path.lower().endswith('.obj'):
            return self.import_obj_furniture()
        else:
            raise ValueError(f"Unsupported file format: {self.model_path}")

    def import_blender_furniture(self):
        with bpy.data.libraries.load(self.model_path, link=False) as (data_from, data_to):
            data_to.objects = [name for name in data_from.objects]
        
        for obj in data_to.objects:
            if obj is not None:
                bpy.context.collection.objects.link(obj)
                obj.location = self.location
                obj.scale = self.scale
                obj.rotation_euler = self.rotation
                obj.name = self.name
        return obj

    def import_obj_furniture(self):
        bpy.ops.wm.obj_import(filepath=self.model_path)  # Updated function to import OBJ files
        imported_objects = bpy.context.selected_objects
        for obj in imported_objects:
            obj.location = self.location
            obj.scale = self.scale
            obj.rotation_euler = self.rotation
            obj.name = self.name
        return imported_objects[0] if imported_objects else None

    def apply_material(self):
        if self.object and hasattr(self.object, 'data') and hasattr(self.object.data, 'materials'):
            mat = bpy.data.materials.new(name=self.name + "_Material")
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            bsdf.inputs['Base Color'].default_value = (0.8, 0.2, 0.3, 1.0)  # RGBA color
            if self.object.data.materials:
                self.object.data.materials[0] = mat
            else:
                self.object.data.materials.append(mat)

# Class for creating a room
class Room:
    def __init__(self, config):
        self.length = config['room']['length']
        self.width = config['room']['width']
        self.height = config['room']['height']
        self.floor_type = config['floor'].get('type', 'default')
        self.floor_type_file = config['floor'].get('path', 'default')
        self.create_floor()
        self.create_walls(config['walls'])
        self.door_material = DoorMaterial("BrownDoorMaterial", (0.396, 0.267, 0.129)).material
        self.add_doors_and_windows(config['doors'], config['windows'])
        self.add_furniture(config['furniture'])

    def create_floor(self):
        bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
        floor = bpy.context.object
        floor.name = "Floor"
        floor.scale[0] = self.length / 2
        floor.scale[1] = self.width / 2

        # Apply material based on floor type
        if self.floor_type == 'wooden':
            mat = bpy.data.materials.new(name="WoodenFloor")
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            tex_image = mat.node_tree.nodes.new("ShaderNodeTexImage")
            tex_type = bpy.data.images.load(self.floor_type_file)
            tex_image.image = tex_type
            mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])
            if floor.data.materials:
                floor.data.materials[0] = mat
            else:
                floor.data.materials.append(mat)
        self.floor = floor
    
    def create_walls(self, walls_config):
        self.walls = {}
        for wall in walls_config:
            color = wall.get('color', [1, 1, 1])  # Default color is white
            new_wall = Wall(wall['name'], wall['location'], wall['scale'], wall['rotation'], color)
            self.walls[wall['name']] = new_wall

    def add_doors_and_windows(self, doors_config, windows_config):
        for door in doors_config:
            self.create_door(door)

        for window in windows_config:
            self.create_window(window)

    def create_door(self, door_config):
        door = DoorWindow(self.walls[door_config['wall']], door_config['name'], door_config['location'], door_config['scale'], self.door_material)

    def create_window(self, window_config):
        window = DoorWindow(self.walls[window_config['wall']], window_config['name'], window_config['location'], window_config['scale'], self.door_material)

    def add_furniture(self, furniture_config):
        self.furniture = {}
        for furniture in furniture_config:
            new_furniture = Furniture(furniture['name'], furniture['model_path'], furniture['location'], furniture['scale'], furniture['rotation'])
            self.furniture[furniture['name']] = new_furniture
class Camera:
    def __init__(self, name, location, rotation):
        self.name = name
        self.location = location
        self.rotation = rotation
        self.object = self.create_camera()
        self.set_camera_view()
    
    def create_camera(self):
        bpy.ops.object.camera_add(location=self.location, rotation=self.rotation)
        camera = bpy.context.object
        camera.name = self.name
        bpy.context.scene.camera = camera  # Set the new camera as the active camera
        return camera

    def set_camera_view(self):
        bpy.context.scene.camera = self.object
        bpy.context.view_layer.objects.active = self.object

    def render(self, filepath):
        bpy.context.scene.render.filepath = filepath
        bpy.ops.render.render(write_still=True)

    
    def set_render_settings(resolution_x=1920, resolution_y=1080, resolution_percentage=100):
        bpy.context.scene.render.resolution_x = resolution_x
        bpy.context.scene.render.resolution_y = resolution_y
        bpy.context.scene.render.resolution_percentage = resolution_percentage

    
    def switch_to_view(view):
        if view == 'TOP':
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            space.region_3d.view_perspective = 'ORTHO'
                            space.region_3d.view_rotation = (1.0, 0.0, 0.0, 0.0)
        elif view == 'FRONT':
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            space.region_3d.view_perspective = 'ORTHO'
                            space.region_3d.view_rotation = (1.0, 0.0, 0.0, 0.0)        



with open("D:/Ced_data/json/newren.json", 'r') as f:
    config = json.load(f)

# Create a room based on the configuration
room = Room(config)

# Switch to Material Preview mode
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'MATERIAL'


# Setting up camera positions for top and front views
camera_top_location = (0, 0, 30)  # Adjust height as needed
camera_top_rotation = (math.radians(360), 0, 0)

camera_front_location = (0, 10, 9)  # Adjust distance and height as needed
camera_front_rotation = (math.radians(50), 0, math.radians(180))

camera_left_location = (-20, 0, 10)  # Adjust distance and height as needed
camera_left_rotation = (math.radians(240),math.radians(180), math.radians(90))

camera_right_location = (20, 0, 10)  # Adjust distance and height as needed
camera_right_rotation = (math.radians(240), math.radians(180), math.radians(-90))

# Create the camera instances
camera_top = Camera("Camera_Top", camera_top_location, camera_top_rotation)
camera_front = Camera("Camera_Front", camera_front_location, camera_front_rotation)

camera_left = Camera("Camera_Left", camera_left_location, camera_left_rotation)
camera_right = Camera("Camera_Right", camera_right_location, camera_right_rotation)

# Set render settings
Camera.set_render_settings()

# Render the top view
camera_top.set_camera_view()
camera_top.render("D:/Ced_data/renders/top_view.png")

# Render the front view
camera_front.set_camera_view()
camera_front.render("D:/Ced_data/renders/front_view.png")

# Render the left view
camera_left.set_camera_view()
camera_left.render("D:/Ced_data/renders/left_view.png")

# Render the right view
camera_right.set_camera_view()
camera_right.render("D:/Ced_data/renders/right_view.png")