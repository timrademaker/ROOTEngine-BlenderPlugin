# ROOTEngine-BlenderPlugin
Blender plugin used for level editing for games made in the ROOT Engine [(more info here)](https://timrademaker.com/portfolio/custom-engine-project-root-engine).

The plugin adds a panel to objects. Opening this panel reveals a drop-down for the object type, and a button to reset the object type. The drop-down is populated with the names of `GameObject` types found in the GameObjectList set in the plugin's settings. This file is a simple text file with the name of a type on each line.

If the selected object is a camera, the panel also contains a button that allows setting the selected camera as the main camera (i.e. the camera the renderer uses by default).


Using the scene in the engine is done by exporting the scene as gltf/glb, with the option "Include Custom Properties" enabled, and then loading the model as a scene in the engine. 
