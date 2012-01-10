### LICENSE BSD ###
# Copyright (c) 2011, Marc Morata && Abel Boldu, Abiquo
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
# * Neither the name of the Abiquo nor the
# names of its contributors may be used to endorse or promote products
# derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL COPYRIGHT HOLDER BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE

import collectd
import os
import time
#import sys
#from subprocess import call

d = {}
hostlist = ([2,2], [2,2])
commandlist = []
clapi = "/usr/share/centreon/www/modules/centreon-clapi/core/centreon"
collectdnagios = "collectd-nagios"

centreon_username = "admin"
centreon_password = "centreon"

# Implement your code to retrieve the hostgroup.
def getHostGroup():
  return "Collectd"

def sendCommand(command):
  c = " -u " + centreon_username + " -p " + centreon_password + " " + command
  # Seems that there are a bug with this code (http://bugs.python.org/issue1731717)
  # try:
  #   retcode = call(clapi + c, shell=True)
  #   if retcode < 0:
  #       print >>sys.stderr, "Child was terminated by signal", -retcode
  #   else:
  #       print >>sys.stderr, "Child returned", retcode
  # except OSError, e:
  #   print >>sys.stderr, "Execution failed:", e
  os.system(clapi + c)

def insertHostGroup(hostgroup, host):
  sendCommand("-o HG -a ADD -v \""+hostgroup+";"+hostgroup+"\"")
  sendCommand("-o HG -a addchild -v \""+hostgroup+";"+host+"\"")

def init():
  #TODO: Check if the commands already exists
  #TODO: Load all the data that already exists in the Centreon

  # Inserting the 2 commands needed to monitor the vms
  sendCommand("-o CMD -a ADD -v 'check_collectd;$USER1$/"+collectdnagios+" -s /opt/collectd/var/run/collectd-unixsock -H $HOSTNAME$ -n $ARG1$;check'")
  sendCommand("-o CMD -a ADD -v 'check_collectd_percentage;$USER1$/"+collectdnagios+" -s /opt/collectd/var/run/collectd-unixsock -H $HOSTNAME$ -n $ARG1$ -g percentage -d $ARG2$ -w $ARG3$ -c $ARG4$;check'")

def write(vl, data=None):
  for i in vl.values:
    if vl.host in d:
      pass
    else:
      hostgroup = getHostGroup()
      d[vl.host]=[]
      # Adding a new  host
      sendCommand("-o HOST -a ADD -v \""+vl.host+";"+vl.host+";0.0.0.0;generic-host;central;Collectd\"")
      # Remove Ping
      # TODO: Fix it because the ping service isn't removed
      sendCommand("-o SERVICE -a del -v \""+vl.host+";ping\"")

      if hostgroup is not None:
        insertHostGroup(hostgroup, vl.host)

    if [vl.plugin,vl.type,vl.plugin_instance,vl.type_instance] in d[vl.host]:
      pass
    else:
      # add service
      d[vl.host].append([vl.plugin,vl.type,vl.plugin_instance,vl.type_instance])
      pluginname = vl.plugin + "/" + vl.type
      if len(vl.plugin_instance) != 0:
        pluginname = vl.plugin + "-" + vl.plugin_instance + "/" + vl.type
      if len(vl.type_instance) != 0:
        pluginname = pluginname + "-" + vl.type_instance
      sendCommand("-o SERVICE -a add -v \""+vl.host+";"+pluginname+";generic-service\"")
      sendCommand("-o SERVICE -a setparam -v \""+vl.host+";"+pluginname+";command;check_collectd\"")
      sendCommand("-o SERVICE -a setparam -v \""+vl.host+";"+pluginname+";normal_check_interval;1\"")
      sendCommand("-o SERVICE -a setparam -v \""+vl.host+";"+pluginname+";retry_check_interval;5\"")
      sendCommand("-o SERVICE -a setparam -v \""+vl.host+";"+pluginname+";check_period;24x7\"")
      sendCommand("-o SERVICE -a setparam -v \""+vl.host+";"+pluginname+";max_check_attempts;5\"")
      sendCommand("-o SERVICE -a setparam -v \""+vl.host+";"+pluginname+";active_checks_enabled;1\"")
      sendCommand("-o SERVICE -a setparam -v \""+vl.host+";"+pluginname+";notif_period;24x7\"")
      sendCommand("-o SERVICE -a setparam -v \""+vl.host+";"+pluginname+";args;!"+pluginname+"!\"")
      sendCommand("-o SERVICE -a setcg -v \""+vl.host+";"+pluginname+";Supervisors\"")

      # Regenerates the centreon configuration
      #TODO: currently we flood the centreon regenerating each service that we add.
      sendCommand("-a POLLERGENERATE -v 1")
      sendCommand("-a CFGMOVE -v 1")
      sendCommand("-a POLLERRELOAD -v 1")
      

collectd.register_init(init);
collectd.register_write(write);
