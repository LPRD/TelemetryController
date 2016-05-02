# -*- mode: python -*-

block_cipher = None


a = Analysis(['static_test_gui.py'],
             pathex=['/media/shared/lrk/U_of_M/Research/LPRD/Telemetry-display/src'],
             binaries=None,
             datas=None,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='static_test_gui',
          debug=False,
          strip=False,
          upx=True,
          console=True )
