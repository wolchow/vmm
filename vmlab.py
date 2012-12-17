# !/usr/bin/env python
# -*- coding: utf-8 -*-

import XenAPI, time, sys
sys.path.append('/home/mif/Dropbox/Diploma/Code')
import thread as thread
import settings,  requests

if settings.vars_dict.get('conn_method') == 'https':
      if settings.vars_dict.get('cert_file'):
            cert_path = settings.vars_dict.get('cert_file')
            try:
                  if cert_path:
                        r = requests.get('https://'+settings.vars_dict.get('xenserver'),  cert=cert_path)
                  else:     
                        r = requests.get('https://'+settings.vars_dict.get('xenserver'))
                  if r.status_code == 200:
                        method = 'https://'
            except requests.exceptions.SSLError:
                  print "Can't connect to %s securely" % (settings.vars_dict.get('xenserver'))
else:
      method = 'http://'

class VMLab:
      url = method+settings.vars_dict.get('xenserver')
      session = XenAPI.Session(url)
      session.login_with_password(settings.vars_dict.get('xenlogin'),  settings.vars_dict.get('xenpwd'))
      
      def __init__(self, VLabName,  id):
            self.Name = VLabName
            self.Id = id
            self.enum()
            self.Count = len(self.vmdict.keys())
            self.cons = {}
            self.error = {}
            
      def enum(self):
            vms = {
                        vm : VMLab.session.xenapi.VM.get_name_label(vm)  #create VMs dictionary  without Xend host itself
                        for vm in VMLab.session.xenapi.VM.get_all() 
                        if not (VMLab.session.xenapi.VM.get_is_a_template(vm) 
                        or VMLab.session.xenapi.VM.get_is_control_domain(vm))}
            self.vmdict = {
                        self.session.xenapi.VM.get_by_name_label(v)[0]  : 
                        self.session.xenapi.VM.get_power_state(self.session.xenapi.VM.get_by_name_label(v)[0])
                        for v in [vm for vm in vms.values() 
                        if self.Id+'_'+self.Name in vm]}
            #self.power_state = [self.session.xenapi.VM.get_power_state(vm) for vm in self.vmlist] #power state of VMs owned by VMLab
     
            
      def start(self):
            try:
                  for vm in self.vmdict.keys():
                        if self.vmdict[vm] == 'Halted':
                              self.session.xenapi.VM.start(vm, False,  True)
                              self.vmdict[vm] = 'Running'
                              self.cons[vm] = self.session.xenapi.console.get_location(self.session.xenapi.VM.get_consoles(vm)[0])
            except Exception as ex:
                  self.error['start'] = str(ex)      
             
      def stop(self):
            try:
                  for vm in self.vmdict.keys():
                        if self.vmdict[vm] == 'Running':
                              self.session.xenapi.Async.VM.clean_shutdown(vm)    
                              self.vmdict[vm] = 'Halted'
            except Exception as ex:
                  self.error ['stop']= str(ex)
                  
      def pause(self):
            try:
                   for vm in self.vmdict.keys():
                        if self.vmdict[vm] == 'Running':
                              self.session.xenapi.Async.VM.pause(vm)
                              self.vmdict[vm] = 'Paused'
            except Exception as ex:
                  self.error['pause'] = str(ex)
                  
      def unpause(self):
            try:
                   for vm in self.vmdict.keys():
                        if self.vmdict[vm] == 'Paused':
                              self.session.xenapi.VM.unpause(vm)
                              self.vmdict[vm] = 'Running'
            except Exception as ex:
                  self.error['unpause'] = str(ex)
             
      def create(self):
#            tags_list = filter(None,  [session.xenapi.VM.get_tags(vm) for vm in session.xenapi.VM.get_all()])
#            my_tags = [(y) for x in tags_list for y in x if self.Name in y]
#            vmt_dict = {
#                              vm : VMLab.session.xenapi.VM.get_name_label(vm) 
#                              for vm in VMLab.session.xenapi.VM.get_all() }
#            if (VMLab.session.xenapi.VM.get_is_a_template(vm)):
#                  pass
            try:
                  tags_dict = {vm : self.session.xenapi.VM.get_tags(vm) for vm in self.session.xenapi.VM.get_all() if self.session.xenapi.VM.get_tags(vm)}
                  vlab_templates_list = [(value ,  items) for items in tags_dict for value in tags_dict[items] if self.Name in value]
                  vlab_templates_list.sort()
                  vmts = filter(lambda x: x[0].startswith('vlab'), vlab_templates_list)
                  netz = filter(lambda x: x[0].startswith('net'), vlab_templates_list)
                  m = [(self.Id+'_'+self.Name+'_'+x[0].split('=>')[1]) for x in vmts]
                  n = [(x[1]) for x in vmts]      
                  temp_list = map(lambda x,y: self.session.xenapi.VM.clone(x, y) , n,m)
                  map(lambda x: self.session.xenapi.VM.set_PV_bootloader(x, 'eliloader') , temp_list)     
                  for vm in temp_list:
#                        for disks in self.session.xenapi.VM.get_VBDs(vm):
#                              if self.session.xenapi.VBD.get_type(disks)=='Disk':
#                                    self.session.xenapi.VBD.set_bootable(disks, True)
                        vmprefix = self.session.xenapi.VM.get_name_label(vm).split('_')[-1]
                        for net in netz: 
                              if vmprefix == net[0].split(':')[-1].split('=>')[0]:
                                    vif = {'device' : self.session.xenapi.VM.get_allowed_VIF_devices(vm)[0],
                                                'network':net[0].split('=>')[-1], 
                                                'VM': vm, 
                                                'MAC':"", 
                                                'MTU':'1500', 
                                                'other_config':{}, 
                                                'qos_algorithm_type': '', 
                                                'qos_algorithm_params':{}}
                                    self.session.xenapi.VIF.create(vif)
                  map(lambda x: self.session.xenapi.VM.set_PV_args(x,  'noninteractive'),  temp_list)
                  map(lambda x: self.session.xenapi.VM.provision(x),  temp_list)
                  self.enum()
                  self.start()
                  #map(lambda x: self.session.xenapi.VM.start(x,  False,  True),  temp_list)
            except Exception as ex:
                  self.error ['create']= str(ex)
 #                  temp_list = map(lambda x,y: self.session.xenapi.Async.VM.clone(x, y) , n,m) #Asyncs work slowly
##                  temp_list = []
##                  def creater(vmlab_name,  obj_ref):
##                        return self.session.xenapi.VM.clone(obj_ref,  vmlab_name) ##threads work less stable and slowly
##                  for i in range(len(vmts)):
##                              t = thread.start_new_thread(creater, (vmts[i]))
##                              time.sleep(5)
##                              temp_list.append(t)
##                  while len(filter(lambda x: x=='success', map(self.session.xenapi.task.get_status, temp_list))) <3:
##                        time.sleep(1)    

#             tags_dict[tags_dict.keys()[0]][1].split('=>')[0].split(':')[1]
#            
#             tags_dict[tags_dict.keys()[0]][0].split(':')[1].split('=>')[1]                     
                  
#             map(lambda x: self.session.xenapi.VM.set_PV_bootloader(x, 'pygrub') , temp_list)           

      def delete(self):
            try:
                   for vm in self.vmdict.keys():
                        if self.vmdict[vm] == 'Halted':
                              self.session.xenapi.VM.destroy(vm)
            except Exception as ex:
                  self.error['delete'] = str(ex)
      
if __name__ == '__main__':

      t = VMLab('UNIX',  'mif')
      t.delete()
      print t.error
      
