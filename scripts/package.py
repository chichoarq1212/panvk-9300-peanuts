#!/usr/bin/env python3
import hashlib, json, pathlib, subprocess, sys, zipfile
so, out, mode, up, mesa = sys.argv[1:]
so, out, up, mesa = map(pathlib.Path, (so,out,up,mesa))
b = so.read_bytes()
assert len(b) > 100000 and b[:6] == b'\x7fELF\x02\x01' and int.from_bytes(b[18:20],'little') == 183, 'Not AArch64 ELF64'
assert int.from_bytes(b[16:18],'little') == 3, 'Not a shared object'
assert mode in ('baseline','e01')
if mode == 'e01': assert b'PANVK9300_E01' in b, 'instrumentation missing'
sha = lambda v: hashlib.sha256(v).hexdigest()
commit = lambda p: subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip()
identity = subprocess.check_output([sys.executable,str(up/'scripts/driver_identity.py'),'--field','driverInfo',str(so)],text=True).strip()
assert identity, 'driver identity missing'
meta = {'schemaVersion':1,'name':f'PANVK-9300-PEANUTS-{mode.upper()}','description':'Experimental rebuild; hardware not validated.','author':'Mesa / Zenithblue contributors; E01 experimental changes','packageVersion':'0.0.1' if mode=='e01' else '0.0.0','vendor':'Mesa','driverVersion':identity,'minApi':29,'libraryName':'libvulkan_panfrost.so'}
provenance = {'upstream':commit(up),'mesa_commit':commit(mesa),'mesa_tree':subprocess.check_output(['git','-C',str(mesa),'rev-parse','HEAD^{tree}'],text=True).strip(),'mode':mode,'sha256':sha(b),'hardware_validation':'NOT_RUN','base_mesa':'5a07217f034b3e50d8c7c7794f97a2df1742613b'}
notice = 'Mesa / PanVK and Zenithblue contributors retain their licenses. Source: https://github.com/zenithblue-oss/panvk-kbase-android ; https://gitlab.freedesktop.org/mesa/mesa . Experimental E01: no hardware validation.\n'
zip_path = out/f'PANVK-9300-PEANUTS-{mode.upper()}.adpkg.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('meta.json',json.dumps(meta,indent=2)+'\n')
    z.writestr('libvulkan_panfrost.so',b)
    z.writestr('NOTICE.txt',notice)
    z.writestr('BUILD-INFO.json',json.dumps(provenance,indent=2)+'\n')
    z.writestr('SHA256SUMS.txt',sha(b)+'  libvulkan_panfrost.so\n')
    for p in [up/'NOTICE.md',mesa/'docs/license.rst']:
        if p.is_file(): z.writestr('LICENSE-'+p.name,p.read_bytes())
    for root in (up, mesa):
        for p in sorted((root/'LICENSES').rglob('*')):
            if p.is_file(): z.writestr('LICENSES/'+('zenith/' if root==up else 'mesa/')+p.relative_to(root/'LICENSES').as_posix(),p.read_bytes())
(out/(zip_path.name+'.sha256')).write_text(sha(zip_path.read_bytes())+'  '+zip_path.name+'\n')
print(zip_path)
