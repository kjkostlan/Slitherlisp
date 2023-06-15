# Some packages have interactions with other packages. cross_package will apply interactions.

def integrate(package_names, package_paths_local):
    if 'Waterworks' in package_names: # Integration with the related Waterworks module:
       import importlib
       py_updater_module = importlib.import_module(package_paths_local['Waterworks']+'.py_updater')

       py_updater_module.Slitherlisp_integration = True
       py_updater_module.record_txt_update_fn = record_txt_updates
       py_updater_module.just_after_module_callback = just_after_module_update
       py_updater_module.get_vars_fn = ppatch.get_vars