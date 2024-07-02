import bpy
import json
import math

# Class for creating a wall
class Wall:
    def __init__(self, name, location, scale, rotation):
        self.name = name
        self.location = location + [0] if len(location) == 2 else location
        self.scale = scale + [1] if len(scale) == 2 else scale
        self.rotation = rotation + [0] if len(rotation) == 2 else rotation
        self.object = self.create_wall()

    def create_wall(self):
        bpy.ops.mesh.primitive_plane_add(size=2, location=self.location)
        wall = bpy.context.object
        wall.name = self.name
        wall.scale[0] = self.scale[0]
        wall.scale[1] = self.scale[1]
        wall.rotation_euler = self.rotation
        return wall

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

# Class for creating a room
class Room:
    def __init__(self, config, floor_location):
        self.length = config['dimensions']['length']
        self.width = config['dimensions']['width']
        self.height = config['dimensions']['height']
        self.floor_type = config['floor'].get('type', 'default')
        self.floor_type_file = config['floor'].get('path', 'default')
        self.create_floor(floor_location, (self.length, self.width))
        self.create_walls(config['walls'])
        self.door_material = DoorMaterial("BrownDoorMaterial", (0.396, 0.267, 0.129)).material
        self.add_doors_and_windows(config['doors'], config['windows'])

    def create_floor(self, location, size, name="Floor"):
        # Add a plane mesh to represent the floor
        bpy.ops.mesh.primitive_plane_add(size=2, location=location)
        floor = bpy.context.object
        floor.name = name

        # Scale the floor to match the specified dimensions
        floor.scale[0] = size[0] / 2
        floor.scale[1] = size[1] / 2

        # Apply material based on floor type
        if self.floor_type == 'wooden':
            # Create a new material named "WoodenFloor"
            mat = bpy.data.materials.new(name="WoodenFloor")
            mat.use_nodes = True

            # Get the Principled BSDF node
            bsdf = mat.node_tree.nodes.get("Principled BSDF")

            # Create a new image texture node and load the texture file
            tex_image = mat.node_tree.nodes.new("ShaderNodeTexImage")
            tex_type = bpy.data.images.load(self.floor_type_file)
            tex_image.image = tex_type

            # Link the image texture to the base color input of the Principled BSDF node
            mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])

            # Assign the material to the floor object
            if floor.data.materials:
                floor.data.materials[0] = mat
            else:
                floor.data.materials.append(mat)
        else:
            print(f"Unknown floor type: {self.floor_type}")

        self.floor = floor

    def create_walls(self, walls_config):
        self.walls = {}
        for wall in walls_config:
            new_wall = Wall(wall['name'], wall['location'], wall['scale'], wall['rotation'])
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

class Toilet:
    def __init__(self, config, location):
        self.length = config['dimensions']['length']
        self.width = config['dimensions']['width']
        self.height = config['dimensions']['height']
        self.floor_type = config['floor'].get('type', 'default')
        self.floor_type_file = config['floor'].get('path', 'default')
        self.create_floor(location, (self.length, self.width))
        self.create_walls(config['walls'])
        self.door_material = DoorMaterial("ToiletDoorMaterial", (0.396, 0.267, 0.129)).material
        self.add_doors_and_windows(config['doors'], config['windows'])

    def create_floor(self, location, size, name="ToiletFloor"):
        # Add a plane mesh to represent the floor
        bpy.ops.mesh.primitive_plane_add(size=2, location=location)
        floor = bpy.context.object
        floor.name = name

        # Scale the floor to match the specified dimensions
        floor.scale[0] = size[0] / 2
        floor.scale[1] = size[1] / 2

        # Apply material based on floor type
        if self.floor_type == 'wooden':
            # Create a new material named "WoodenFloor"
            mat = bpy.data.materials.new(name="WoodenFloor")
            mat.use_nodes = True

            # Get the Principled BSDF node
            bsdf = mat.node_tree.nodes.get("Principled BSDF")

            # Create a new image texture node and load the texture file
            tex_image = mat.node_tree.nodes.new("ShaderNodeTexImage")
            tex_type = bpy.data.images.load(self.floor_type_file)
            tex_image.image = tex_type

            # Link the image texture to the base color input of the Principled BSDF node
            mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])

            # Assign the material to the floor object
            if floor.data.materials:
                floor.data.materials[0] = mat
            else:
                floor.data.materials.append(mat)
        else:
            print(f"Unknown floor type: {self.floor_type}")

        self.floor = floor

    def create_walls(self, walls_config):
        self.walls = {}
        for wall in walls_config:
            new_wall = Wall(wall['name'], wall['location'], wall['scale'], wall['rotation'])
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

# Load the configuration file
with open("D:\Ced_data\data-prefinal.json", 'r') as f:
    config = json.load(f)

# Create rooms based on the configuration
room1 = Room(config['room1'], (0, 0, 0))
room2 = Room(config['room2'], (20,-4, 0))  
room3 = Room(config['room3'], (20,4,0))
room4 = Room(config['studyroom'],(-8,12,0))
room5 = Room(config['bigroom'],(1,0,0))
# Create a toilet based on the configuration
toilet = Toilet(config['toilet1'], (27,-6, 0))  
toilet = Toilet(config['toilet2'], (27,5,0))
# Switch to Material Preview mode
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'MATERIAL'