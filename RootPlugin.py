import bpy
from bpy.app.handlers import persistent

bl_info = {
    "name": "ROOT Add-On",
    "author": "Tim Rademaker",
    "description": "A plugin to help with level editing for the ROOT engine",
    "version": (0, 3, 2),
    "blender": (2, 80, 0),
    "category": "Object",
}

type_tag_key : str = "ObjectType"
main_camera_tag : str = "IsMainCamera" 


''' Add-on Preferences '''
class ROOT_RootAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    
    root_gameobject_list: bpy.props.StringProperty(
        name="ROOT Project GameObject List",
        subtype="FILE_PATH",
        description="The path to the GameObject type list. This file is usually located in the working directory of the project"
    )
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "root_gameobject_list")
        layout.operator("object.root_update_gameobject_types_operator")    
        layout.operator("object.root_remove_nonexisting_gameobject_types_operator")    


''' Operator classes '''
class ROOT_ResetGameObjectTypeOperator(bpy.types.Operator):
    """Clicking this resets the selected Game object type, making this object a default GameObject"""
    bl_idname = "object.root_reset_gameobject_type_operator"
    bl_label = "Reset GameObject Type"
    
    def execute(self, context):
        remove_go_type(context)
        return {'FINISHED'}
    
    
class ROOT_UpdateGameObjectTypesOperator(bpy.types.Operator):
    """Update the list of GameObject types that Blender knows about"""
    bl_idname = "object.root_update_gameobject_types_operator"
    bl_label = "Update GameObject Types"
    
    def execute(self, context):
        bpy.types.Scene.root_should_remove_unused_types = False
        set_gameobject_type_enum()
        bpy.types.Scene.root_should_remove_unused_types = True
        return {'FINISHED'}
    
    
class ROOT_RemoveNonexistingGameObjectTypes(bpy.types.Operator):
    """Remove custom properties from objects that use a GameObject type that no longer exists"""
    bl_idname = "object.root_remove_nonexisting_gameobject_types_operator"
    bl_label = "Remove Non-Existing GameObject Types"
    
    def execute(self, context):
        if bpy.types.Scene.root_should_remove_unused_types:
            for obj in bpy.context.scene.objects:
                if type_tag_key in obj:
                    if not type_exists_in_type_enum(obj[type_tag_key]):
                        del obj[type_tag_key]
        else:
            print("[ROOT Plugin] Please update the GameObject type list before doing this!")
        return {'FINISHED'}


class ROOT_SetAsMainCamera(bpy.types.Operator):
    """Set the current object as the main camera to use"""
    bl_idname = "object.root_set_main_camera"
    bl_label = "Set as Main Camera"
    
    def execute(self, context):
        print(context.active_object.type)
        if context.active_object.type.lower() in ['camera']:
            all_objects = context.scene.items()
            for obj in all_objects:
                if hasattr(obj, main_camera_tag):
                    del obj[main_camera_tag]
                    break
        
            context.active_object[main_camera_tag] = True
        return {'FINISHED'}


''' Panel class '''
class ROOT_RootPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "ROOT Panel"
    bl_idname = "OBJECT_PT_root_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    
    def draw(self, context):        
        layout = self.layout
        
        try:
            if bpy.types.Scene.root_gameobject_type_enum:
                pass
        except:
            row = layout.row()
            row.label(text="Did you set the ROOT GameObject list directory in the Add-On preferences correctly?")
            row = layout.row()
            row.label(text="Currently set to \"{file}\"".format(file=gameobject_type_file_name()))
            row = layout.row()
            row.label(text="Don't forget to click \"Update\"")
            
            return

        obj = context.object

        row = layout.row()
        row.label(text="GameObject Type Selection", icon='ROOTCURVE')

        row = layout.row()
        
        row.prop(data=context.scene, property='root_gameobject_type_enum', text="Object Type", icon='GHOST_ENABLED')
        
        row = layout.row()
        row.operator("object.root_reset_gameobject_type_operator")
        
        if context.active_object.type.lower() in ['camera']:
            row = layout.row()
            row.operator("object.root_set_main_camera")
        
 
 
''' Other classes '''
class ROOT_MsgBusOwner():
    instance = None
     
    @staticmethod
    def get_instance():
        if ROOT_MsgBusOwner.instance is not None:
            ROOT_MsgBusOwner.instance = ROOT_MsgBusOwner()
        return ROOT_MsgBusOwner.instance
    
    @staticmethod
    def subscribe(dummy1 = None, dummy2 = None):
        bpy.msgbus.subscribe_rna(
            key=bpy.types.LayerObjects
            , owner=ROOT_MsgBusOwner.get_instance()
            , args=()
            , notify=set_type_enum_preview_to_selected_value
        )
     
    @staticmethod
    def unsubscribe(dummy1 = None, dummy2 = None):
        if ROOT_MsgBusOwner.instance is not None:
            bpy.msgbus.clear_by_owner(ROOT_MsgBusOwner.instance)
 
 
''' Functions '''
def prefs():
    return bpy.context.preferences.addons[__name__].preferences


def gameobject_type_file_name():    
    return prefs().root_gameobject_list


def get_gameobject_type_list() -> list:
    ent_types: list = []
    try:
        root_go_type_file = open(gameobject_type_file_name(), "r")
        file_content = root_go_type_file.read()
        root_go_type_file.close()
        
        ent_types = file_content.split("\n")
        if ent_types[-1] == '':
            ent_types = ent_types[:-1]
    except IOError as e:
        print("[ROOT Plugin] Something went wrong when reading from the GameObject type list! Is the path to the file correct? ({path})".format(path=gameobject_type_file_name()))
    
    return ent_types
   
        
def on_gameobject_type_update(self, context):
    if self.root_gameobject_type_enum != "None":
        context.active_object[type_tag_key] = self.root_gameobject_type_enum
    else:
        if bpy.types.Scene.root_should_remove_unused_types:
            remove_go_type(context)
    return None
    
    
def remove_go_type(context: bpy.types.Context = bpy.context):
    if type_tag_key in context.active_object:
        del context.active_object[type_tag_key]
        context.scene.root_gameobject_type_enum = "None"
    
    
def type_exists_in_type_enum(type_name: str) -> bool:
    # Get all enum identifiers
    if hasattr(bpy.context, "scene"):
        props = bpy.context.scene.bl_rna.properties['root_gameobject_type_enum']
        enum_identifiers = [e.identifier for e in props.enum_items]
    else:
        return False
    
    return type_name in enum_identifiers


def set_type_enum_preview_to_selected_value():
    if not hasattr(bpy.context, "scene") or not hasattr(bpy.context, "active_object"):
        return

    if hasattr(bpy.context, 'active_object') and bpy.context.active_object is not None and type_tag_key in bpy.context.active_object:
        currently_selected_type = bpy.context.active_object[type_tag_key]
    else:
        currently_selected_type = "None"
    if not type_exists_in_type_enum(currently_selected_type):
        currently_selected_type = "None"


    bpy.context.scene.root_gameobject_type_enum = currently_selected_type


def set_gameobject_type_enum():
    # Read all GameObject type names from the file
    root_type_enum: list = [("None", "None", '', -1)]
    
    root_go_type_names: list = get_gameobject_type_list()

    for i in range(0, len(root_go_type_names)):
        n: str = root_go_type_names[i]
        root_type_enum.append((n, n, '', i))
        
    bpy.types.Scene.root_gameobject_type_enum = bpy.props.EnumProperty(items=root_type_enum, update=on_gameobject_type_update, default="None")
    set_type_enum_preview_to_selected_value()

    bpy.types.Scene.root_should_remove_unused_types = True
    
    
''' (Un)Registration functions '''
def register():
    bpy.app.handlers.load_post.append(ROOT_MsgBusOwner.subscribe)
    bpy.app.handlers.depsgraph_update_post.append(ROOT_MsgBusOwner.subscribe)
    ROOT_MsgBusOwner.subscribe()

    print("[ROOT Plugin] Initialzing ROOT plugin")
    
    bpy.types.Scene.root_should_remove_unused_types = False
    
    bpy.utils.register_class(ROOT_RemoveNonexistingGameObjectTypes)
    bpy.utils.register_class(ROOT_UpdateGameObjectTypesOperator)
    bpy.utils.register_class(ROOT_RootAddonPreferences)
    bpy.utils.register_class(ROOT_ResetGameObjectTypeOperator)
    bpy.utils.register_class(ROOT_SetAsMainCamera)
    bpy.utils.register_class(ROOT_RootPanel)
    
    if prefs().root_gameobject_list is "":
        print("[ROOT Plugin] Please set your ROOT GameObject type list in the add-on preferences!")
    else:
        set_gameobject_type_enum()

    
def unregister():
    print("[ROOT Plugin] Uninitialzing ROOT plugin")
    
    bpy.utils.unregister_class(ROOT_RootPanel)
    bpy.utils.unregister_class(ROOT_ResetGameObjectTypeOperator)
    bpy.utils.unregister_class(ROOT_RootAddonPreferences)
    bpy.utils.unregister_class(ROOT_UpdateGameObjectTypesOperator)
    bpy.utils.unregister_class(ROOT_SetAsMainCamera)
    bpy.utils.unregister_class(ROOT_RemoveNonexistingGameObjectTypes)
    
    if hasattr(bpy.types.Scene, 'root_gameobject_type_enum'):
        del bpy.types.Scene.root_gameobject_type_enum
        
    if hasattr(bpy.types.Scene, 'root_should_remove_unused_types'):
        del bpy.types.Scene.root_should_remove_unused_types
        
    ROOT_MsgBusOwner.unsubscribe()
    if ROOT_MsgBusOwner.subscribe in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(ROOT_MsgBusOwner.subscribe)
        
    if ROOT_MsgBusOwner.subscribe in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(ROOT_MsgBusOwner.subscribe)

    
if __name__ == "__main__":
    register()
