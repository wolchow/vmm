# !/usr/bin/env python
# -*- coding: utf-8 -*-

def main(vars_dict):
      srv = vars_dict.get('xenserver', 'localhost') #setting variables
      login = vars_dict.get('xenlogin', 'root')
      pwd = vars_dict.get('xenpwd', 'password')
      action = vars_dict.get('action', 'get_info')
      stud_login = vars_dict.get('stud_login', 'mif')
      template = vars_dict.get('template', 'CentOS_TEST')
      ldap_server = vars_dict.get('ldapserver')
      DN = vars_dict.get('DN')
      Secret = vars_dict.get('Secret')
      BASE = vars_dict.get('BASE')
      vmname = stud_login+'_'+template
      session = conn(srv, login, pwd)
      if (session > 0):
            if action == 'get_info':
                  return session.xenapi.VM.get_record(vmname)
            if action == 'clone':
                  try:
                        vm = clone(session, stud_login, template)
                        change_state(session, vm, 'start')
                  except Exception as ex:
                        print "Couldn't clone VM from template\nvmm.clone() process throw an exception:\n",  ex 
            if action in ['start',  'stop',  'pause', 'unpause', 'hard_shutdown', 'reboot']:
                  vm = session.xenapi.VM.get_by_name_label(vmname)[0]
                  change_state(session,  vm,  action)
            atexit.register(logout,  session)
      else:
            print "Couldn't connect to %s",  server
 
def change_state(session, vm, action):
      '''Changing Virtual Machine's state'''
      state = session.xenapi.VM.get_power_state(vm)
      name_label = session.xenapi.VM.get_name_label(vm)
      if (action,  state) == ('start',  'Halted'):
            try:
                   session.xenapi.VM.start(vm, False,  True) 
                   print 'VM %s has started' % (name_label)
                   cons = session.xenapi.VM.get_consoles(vm)[0]
                   vnc_connector = session.xenapi.console.get_location(cons)
                   return vnc_connector
            except Exception as ex:
                  print "Can't start VM %s\nCurrent state is %s\nvmm.change_state() throw an exception:\n%s" % (name_label,  state,  ex)  

      elif (action,  state) == ('stop', 'Running'):
            try:
                   task = session.xenapi.Async.VM.clean_shutdown(vm)
                   print 'VM %s is stopped' % (name_label)
            except Exception as ex:
                  print "Can't stop VM %s\nCurrent state is %s\nvmm.change_state() throw an exception:\n%s" % (name_label,  state,  ex) 

      elif (action,  state) == ('reboot', 'Running'):
            try:
                   task = session.xenapi.Async.VM.clean_reboot(vm)
                   print 'VM %s going to reboot now' % (name_label)
            except Exception as ex:
                  print "Can't reboot VM %s\nCurrent state is %s\nvmm.change_state() throw an exception:\n%s" % (name_label,  state,  ex) 

      elif (action, state) == ('pause', 'Running'):
            try:
                   task = session.xenapi.Async.VM.pause(vm)
                   print 'VM %s is paused' % (name_label)
            except Exception as ex:
                  print "Can't pause VM %s\nCurrent state is %s\nvmm.change_state() throw an exception:\n%s" % (name_label,  state,  ex) 

      elif (action, state) == ('unpause', 'Paused'):
            try:
                   task = session.xenapi.Async.VM.unpause(vm)
                   print 'VM %s is running' % (name_label)
            except Exception as ex:
                  print "Can't unpause VM %s\nCurrent state is %s\nvmm.change_state() throw an exception:\n%s" % (name_label,  state,  ex) 
      
      elif (action,  state) == ('hard_shutdown', 'Running'):
            try:
                   session.xenapi.VM.hard_shutdown(vm)
                   print 'VM %s has shutdown unclean' % (name_label)
            except Exception as ex:
                  print "Can't shutdown VM %s\nCurrent state is %s\nvmm.change_state() throw an exception:\n%s" % (name_label,  state,  ex) 
      
#      if task:
#            print 'Async call "%s" exited with status %s' % (session.xenapi.task.get_record(task)['name_label'], session.xenapi.task.get_record(task)['status'])
#            time.sleep (3)
#            print 'Async call "%s" has status %s' % (session.xenapi.task.get_record(task)['name_label'], session.xenapi.task.get_record(task)['status'])
      
#      elif action == 'resume':
#            try:
#                  if state == 'Suspended':
#                        session.xenapi.VM.resume(vm,  False, True) # start_paused = False, force = True
#            except Exception as ex:
#                   print "Can't resume VM %s\nCurrent state is %s\nvmm.change_state() throw an exception:\n%s" % (name_label,  state,  ex)      
      
def logout(session):
      try:
            session.xenapi.session.logout()
      except:
            pass

def clone(session, stud_login,  template):
      '''function to clone VM from template'''
      exist = session.xenapi.VM.get_by_name_label(stud_login + '_' + template)
      if exist:
            vmname = exist[0]
            return (vmname)
      else:
            ldap_mod =ldap_modifier_deco(ldap_search) 
            ldap_mod(stud_login) # setting 'description'-attribute in user properties in LDAP/AD
            vms = {vm : session.xenapi.VM.get_record(vm) for vm in session.xenapi.VM.get_all() if session.xenapi.VM.get_is_a_template(vm)}            #templates_dict_creation
            name_label = { vm : session.xenapi.VM.get_name_label(vm) for vm in vms.keys()} 
            if template in name_label.values():
                  print "Try to clone VM from %s to %s " % (template, stud_login)
                  ref_template = session.xenapi.VM.get_by_name_label(template)[0]
                  vmt = session.xenapi.VM.clone(ref_template, stud_login + '_' + template)
                  print "New VM has name %s" % (stud_login + '_' + template)
                  session.xenapi.VM.set_PV_args(vmt,  'noninteractive')
                  pool = session.xenapi.pool.get_all()[0]
                  default_sr = session.xenapi.pool.get_default_SR(pool)
                  default_sr = session.xenapi.SR.get_record(default_sr)
                  session.xenapi.VM.provision(vmt)
                  return vmt

def conn(server, service_login, service_pwd):
      try:
            url = 'http://'+server
            session = XenAPI.Session(url)
            session.xenapi.login_with_password(service_login, service_pwd)
            return session
      except Exception as ex:
            print ex         
 
def ldap_modifier_deco(ldap_search):
      ''' Decorate base ldap_search() func to possible making changes in attributes'''
      def wrapper(stud_login):
            l,  r = ldap_search(stud_login)
            old = {'description' : r[0][1].get('description', '')}
            new = {'description' : r[0][1].get('sAMAccountName')[0]+'_'+vars_dict.get('template')} #local var better, than global?
            ldif = modlist.modifyModlist(old,new)
            dn = r[0][1].get('distinguishedName')[0]
            l.modify_s(dn,ldif)
            l.unbind_s()
      return wrapper

def ldap_search(stud_login,  
      ldap_server , DN , Secret, Base ):
      '''Find user in AD, check account status (should be not in disable state)'''      
      Scope = ldap.SCOPE_SUBTREE
      Filter = "(&(sAMAccountname="+stud_login+")(!(userAccountControl:1.2.840.113556.1.4.803:=2)))"
      l = ldap.initialize(ldap_server)
      l.protocol_version = 3
      l.network_timeout = 5
      l.simple_bind_s(DN,  Secret)
      l.set_option(ldap.OPT_REFERRALS,  0)
      r = l.search_st(Base, Scope, Filter,  timeout=5)
      return l,  r[:1]

if  __name__ == '__main__':
      import XenAPI,  atexit,  time
      import ldap,  os,  sys
      import  ldap.modlist as modlist 
      try:
            import settings #import default settings for vmm.py as dictionary
      except Exception as ex:
            print 'Bad config file settings.py'
            print 'Exception: %s' % (ex)
      main(settings.vars_dict)
