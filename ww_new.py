# !/usr/bin/env python
# -*- coding: utf-8 -*-

import cherrypy
import vmlab
import sys
import valid_courses_list

class RESTResource(object):
   """
   Base class for providing a RESTful interface to a resource.

   To use this class, simply derive a class from it and implement the methods
   you want to support.  The list of possible methods are:
   handle_GET
   handle_PUT
   handle_POST
   handle_DELETE
   """
   @cherrypy.expose
   def default(self, *vpath, **params):
      method = getattr(self, "handle_" + cherrypy.request.method, None)
      if not method:
            methods = [x.replace("handle_", "")
            for x in dir(self) if x.startswith("handle_")]
            cherrypy.response.headers["Allow"] = ",".join(methods)
            raise cherrypy.HTTPError(405, "Method not implemented.")
      return method(*vpath, **params);

class VMResource(RESTResource):
      def handle_GET(self, *vpath, **params):
            if filter(None,  [vpath[0] in valid_courses_list.courses] ):
                  vlabname,  id = vpath
            else:
                  vlabname = params.get('vmlab')
                  id = params.get('id')
            if (vlabname and id):
                  vl = vmlab.VMLab(vlabname,  id)
                  return '<br/>'.join(vl.cons.values())
            raise cherrypy.HTTPError(404,  "Not Found") 
      
      def handle_POST(self, *vpath,  **params):
            vlabname,  id = vpath
            if params.has_key('action'):
                  action = params['action']
                  vl = vmlab.VMLab(vlabname,  id)
                  if action == 'clone':
                        vl.create()
                        if not vl.error: 
                              cherrypy.response.headers["Status"]  = '201'
                              return 'Created'
                              raise cherrypy.HTTPError(400, "Bad request")
                  elif action =='start':
                        vl.start()
                        if not vl.error: 
                              cherrypy.response.headers["Status"]  = '202'
                              return 'Accepted'
                  elif action == 'stop':
                        vl.stop()
                        if not vl.error: 
                              cherrypy.response.headers["Status"]  = '202'
                              return 'Accepted'
                  else:
                        raise cherrypy.HTTPError(400, "Bad request")
                        
      def handle_PUT(self, *vpath,  **params):
            vlabname,  id = vpath
            if params.has_key('action'):
                  action = params['action']
                  vl = vmlab.VMLab(vlabname,  id)
                  if action == 'pause':
                        vl.pause()
                        if not vl.error: 
                              cherrypy.response.headers["Status"]  = '202'
                              return 'Accepted'
                  elif action =='unpause':
                        vl.unpause()
                        if not vl.error: 
                              cherrypy.response.headers["Status"]  = '202'
                              return 'Accepted'
                  raise cherrypy.HTTPError(400, "Bad request")
                  
      def handle_DELETE(self, *vpath,  **params):
            vlabname,  id = vpath
            vl = vmlab.VMLab(vlabname,  id)
            vl.delete()
            if not vl.error: 
                  cherrypy.response.headers["Status"]  = '202'
                  return 'Accepted'
            raise cherrypy.HTTPError(404,  "Not Found") 
 
 
class VMLab(object):
      VM = VMResource()

#    @cherrypy.expose
#    def index(self):
#        return "It's working!"
        
cherrypy.quickstart(VMLab()) 
