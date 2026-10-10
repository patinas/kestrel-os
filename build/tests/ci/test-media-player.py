"""Disposable VM MPRIS player fixture, never installed in the shipped profile."""
import json,sys
from pathlib import Path
from gi.repository import Gio,GLib
log=Path(sys.argv[1]);events=[];play='Paused'
xml='''<node><interface name="org.mpris.MediaPlayer2.Player"><method name="PlayPause"/><method name="Next"/><method name="Previous"/><property name="PlaybackStatus" type="s" access="read"/><property name="CanControl" type="b" access="read"/><property name="CanPlay" type="b" access="read"/><property name="CanPause" type="b" access="read"/><property name="CanGoNext" type="b" access="read"/><property name="CanGoPrevious" type="b" access="read"/></interface></node>'''
bus=Gio.bus_get_sync(Gio.BusType.SESSION,None)
def call(conn,sender,path,interface,method,parameters,invocation):
 global play
 if method=='PlayPause':play='Playing' if play=='Paused' else 'Paused'
 events.append(method);log.write_text(json.dumps({'events':events,'playback':play}));invocation.return_value(None)
def prop(conn,sender,path,interface,name):return GLib.Variant('s',play) if name=='PlaybackStatus' else GLib.Variant('b',True)
bus.register_object('/org/mpris/MediaPlayer2',Gio.DBusNodeInfo.new_for_xml(xml).interfaces[0],call,prop,None)
Gio.bus_own_name_on_connection(bus,'org.mpris.MediaPlayer2.kestrel_ci',Gio.BusNameOwnerFlags.NONE,None,None)
log.write_text(json.dumps({'events':[],'playback':play}));GLib.MainLoop().run()
