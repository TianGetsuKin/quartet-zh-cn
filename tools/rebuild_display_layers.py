"""Rebuild dependent native display layers after base metadata changes."""
import subprocess,sys,json,hashlib
from asset_support import ROOT,GAME
report=json.loads((ROOT/'qa/private-controls-candidate.json').read_text(encoding='utf-8'))
assert hashlib.sha256((GAME.parent/'GameAssembly.dll').read_bytes()).hexdigest()==report['native_original_sha256'],'Restore complete localization before rebuilding layers'
for script in ['build_private_control_strings.py','verify_private_control_strings.py','build_name_display_stub.py','verify_name_display_stub.py','build_save_name_adapter.py','build_name_display_candidate.py','verify_name_display_candidate.py']:
 if script=='build_name_display_candidate.py':subprocess.run([sys.executable,'-X','utf8',str(ROOT/'tools/verify_name_display_stub.py'),'--save-adapter'],check=True)
 subprocess.run([sys.executable,'-X','utf8',str(ROOT/'tools'/script)],check=True)
for script in ['build_location_display_converter.py','build_location_callback_adapters.py','verify_location_callback_adapters.py','build_saved_location_split_adapter.py','verify_saved_location_split_adapter.py','build_saved_location_fallback.py','verify_saved_location_fallback.py','build_autosave_location_bridge.py','verify_autosave_location_bridge.py','build_location_display_candidate.py','verify_location_display_candidate.py']:
 if script=='build_location_callback_adapters.py':subprocess.run([sys.executable,'-X','utf8',str(ROOT/'tools/verify_name_display_stub.py'),'--locations'],check=True)
 subprocess.run([sys.executable,'-X','utf8',str(ROOT/'tools'/script)],check=True)
for script in ['build_dialogue_title_converter.py','verify_dialogue_title_converter.py','build_dialogue_title_adapter.py','verify_dialogue_title_adapter.py','build_settings_value_adapters.py','verify_settings_value_adapters.py','build_dialogue_title_candidate.py','verify_dialogue_title_candidate.py']:
 subprocess.run([sys.executable,'-X','utf8',str(ROOT/'tools'/script)],check=True)
print('All settings, names, locations and dialogue title display layers rebuilt and checked.')
