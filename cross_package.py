# Some packages have interactions with other packages. cross_package will apply interactions.

def integrate(package_paths_local):
    package_paths_local = dict(zip([pname.lower() for pname in package_paths_local.keys()], package_paths_local.values()))
    if 'waterworks' in package_paths_local: # Integration with the related Waterworks module:
       import importlib
       from . import var_watch, ppatch

       py_updater_module = importlib.import_module(package_paths_local['waterworks']+'.py_updater')

       py_updater_module.Slitherlisp_integration = True
       py_updater_module.record_txt_update_fn = var_watch.record_txt_update
       py_updater_module.just_after_module_callback = var_watch.just_after_module_update
       py_updater_module.get_vars_fn = ppatch.get_vars
