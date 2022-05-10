import bpy

importer = {
    'usd': 'wm.usd_import',
    'usdc': 'wm.usd_import',
    'usda': 'wm.usd_import',

    'ply': 'import_mesh.ply',
    'stl': 'import_mesh.stl',
    'dae': 'wm.collada_import',
    'abc': 'wm.alembic_import',
    'obj': 'import_scene.obj',
    'fbx': 'import_scene.fbx',

    'glb': 'import_scene.gltf',
    'gltf': 'import_scene.gltf',

    'x3d': 'import_scene.x3d',
    'wrl': 'import_scene.x3d',

    'svg': 'import_curve.svg',
    'dxf': 'import_scene.dxf',
    'vdb': 'object.volume_import'
}


def get_importer(cpp_obj_importer=True):
    im = importer.copy()
    if cpp_obj_importer and bpy.app.version >= (3, 2, 0):
        im['obj'] = 'wm.obj_import'

    return im
