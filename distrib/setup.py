import sys, os
if sys.platform == "win32": # For py2exe.
    try :
        import modulefinder
        import win32com
        for p in win32com.__path__[1:]:
            modulefinder.AddPackagePath( 'win32com', p )
        for extra in ['win32com.shell'] :
            __import__( extra )
            m = sys.modules[extra]
            for p in m.__path__[1:] :
                modulefinder.AddPackagePath( extra, p )
    except ImportError :
        pass
    
    sys.path.insert( 0, os.path.join(os.path.split(__file__)[0],'..') )
    
    from distutils.core import setup
    import py2exe
    dll_excludes = [
		'MSVCP90.dll',
		'OLEAUT32.dll',
		'USER32.dll',
		'SHELL32.dll',
		'KERNEL32.dll',
		'WINMM.dll',
		'WSOCK32.dll',
		'COMDLG32.dll',
		'ADVAPI32.dll',
		'COMCTL32.dll',
		'WS2_32.dll',
		'GDI32.dll',
		'RPCRT4.dll',
		'ole32.dll',
	]
    opts = {
        'py2exe' : {
    #        'includes' : 'sip',
            'optimize': 1, # 0 (None), 1 (-O), 2 (-OO)
			'dll_excludes' : dll_excludes,
    #        'ignores' : 'ncrypt.digest,ncrypt.cipher,ncrypt.rand,ncrypt.rsa,ncrypt.x509,ncrypt.ssl'
        }
    }
    
    kmappyApp = {
        'script' : '../blam.py',
        'icon_resources' : [(1,'../wxwin.ico')]
        }
    
    
    apps = [kmappyApp]
    #apps.extend( [imApp] )
    #apps.extend( [fileSenderApp,fileReceiverApp] )
    #apps.extend( [vncClientApp,vncServerApp] )
    setup(
            options=opts,
			version='1.0',
    		windows=apps
            )
